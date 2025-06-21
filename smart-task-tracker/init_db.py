import sqlite3

conn = sqlite3.connect('tasks.db')  # This creates the DB file
c = conn.cursor()

# Create users table
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Create tasks table
c.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    due DATE,
    category TEXT,
    priority TEXT,
    tags TEXT,
    done INTEGER DEFAULT 0,
    email TEXT,
    user_id INTEGER,
    reminder_sent INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

conn.commit()
conn.close()
print("✅ Database initialized successfully!")
