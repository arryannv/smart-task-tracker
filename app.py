from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
import os
from flask import Flask, render_template, request, redirect, url_for
from ollama import Client
from flask import jsonify
import ollama
from openai import OpenAI
from dotenv import load_dotenv

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  
)

app = Flask(__name__)
load_dotenv()
# Defining the client here
ollama_client = Client(host='http://localhost:11434')

app = Flask(__name__)

# ---------------------------- EMAIL CONFIG ----------------------------
sender_email = os.getenv('EMAIL_USER')
app_password = os.getenv('EMAIL_PASS')

def send_email(recipient, subject, body):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)

def get_pending_tasks():
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT title, due, category FROM tasks WHERE done = 0")
    tasks = cursor.fetchall()
    conn.close()
    return tasks



# ---------------------------- REMINDER SCHEDULER ----------------------------
def send_reminders():
    today = datetime.now().date()
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM tasks 
        WHERE done = 0 
          AND email IS NOT NULL 
          AND email != '' 
          AND reminder_sent = 0
    """)
    tasks = cursor.fetchall()
    for task in tasks:
        due_date = datetime.strptime(task['due'], '%Y-%m-%d').date()
        if due_date == today:
            try:
                subject = "🔔 Task Reminder"
                body = f"Reminder: '{task['title']}' is due today.\n\nDescription: {task['description']}"
                send_email(task['email'], subject, body)
                cursor.execute('UPDATE tasks SET reminder_sent = 1 WHERE id = ?', (task['id'],))
                print(f"✅ Email sent to {task['email']} for task: {task['title']}")
            except Exception as e:
                print(f"❌ Failed to send reminder for task {task['id']}: {e}")
            break
    conn.commit()
    conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(send_reminders, 'interval', minutes=1)


# ---------------------------- ROUTES ----------------------------

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form['message']

    # Fetch pending tasks
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT title, description, due FROM tasks WHERE done = 0")
    tasks = c.fetchall()
    conn.close()

    # Format tasks into context
    if tasks:
        task_list = "\n".join(
            [f"- {task['title']} (Due: {task['due'] or 'No due date'})" for task in tasks]
        )
        task_context = f"Here are the user's actual pending tasks:\n{task_list}\n\nOnly refer to these tasks when answering."
    else:
        task_context = "The user has no pending tasks."

    # AI call
    response = client.chat.completions.create(
        model="llama3",
        messages=[
            {"role": "system", "content": "You are a task assistant. Only refer to the tasks listed in the assistant message. Do NOT make up or suggest new tasks unless explicitly asked."},
            {"role": "assistant", "content": task_context},
            {"role": "user", "content": user_message}
        ]
    )

    reply = response.choices[0].message.content
    return jsonify({'reply': reply})


@app.route('/', methods=['GET'])
def index():
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', 'all')
    due_filter = request.args.get('due', 'all')
    search_query = request.args.get('q', '')
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if status_filter != 'all':
        query += " AND done = ?"
        params.append(1 if status_filter == 'completed' else 0)
    if category_filter != 'all':
        query += " AND category = ?"
        params.append(category_filter)
    if due_filter == 'today':
        today = str(datetime.now().date())
        query += " AND due = ?"
        params.append(today)
    if search_query:
        query += " AND (title LIKE ? OR description LIKE ?)"
        like_query = f"%{search_query}%"
        params.extend([like_query, like_query])
    c.execute(query, params)
    tasks = c.fetchall()
    conn.close()
    return render_template('index.html',
                           tasks=tasks,
                           status_filter=status_filter,
                           category_filter=category_filter,
                           due_filter=due_filter,
                           search_query=search_query)

@app.route('/add', methods=['POST'])
def add_task():
    title = request.form['title']
    description = request.form['description']
    due = request.form['due']
    category = request.form['category']
    priority = request.form['priority']
    email = request.form.get('email', '')
    tags = request.form.get('tags', '')
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('''INSERT INTO tasks (title, description, due, category, priority, email, tags, done, reminder_sent)
                 VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)''',
              (title, description, due, category, priority, email, tags))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/complete/<int:task_id>')
def complete(task_id):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('UPDATE tasks SET done = 1 WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete(task_id):
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM tasks')
    total = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM tasks WHERE done = 1')
    completed = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM tasks WHERE done = 0')
    pending = c.fetchone()[0]

    c.execute('SELECT category, COUNT(*) as count FROM tasks GROUP BY category')
    categories = c.fetchall()

    c.execute('SELECT COUNT(*) FROM tasks WHERE due = ?', (str(datetime.now().date()),))
    due_today = c.fetchone()[0]

    conn.close()
    return render_template('dashboard.html', total=total, completed=completed, pending=pending,
                           categories=categories, due_today=due_today)

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit(task_id):
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due = request.form['due']
        category = request.form['category']
        priority = request.form['priority']
        tags = request.form['tags']
        email = request.form['email']

        c.execute('''
            UPDATE tasks SET title=?, description=?, due=?, category=?, 
            priority=?, tags=?, email=? WHERE id=?
        ''', (title, description, due, category, priority, tags, email, task_id))

        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    # GET request - load existing data
    c.execute('SELECT * FROM tasks WHERE id=?', (task_id,))
    task = c.fetchone()
    conn.close()
    return render_template('edit.html', task=task)


if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler.start()
    app.run(debug=True)
