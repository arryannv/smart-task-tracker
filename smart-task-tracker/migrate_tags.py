import sqlite3

conn = sqlite3.connect('tasks.db')
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE tasks ADD COLUMN tags TEXT")
    print("✅ 'tags' column added successfully.")
except sqlite3.OperationalError as e:
    print(f"⚠️ {e}")  # Will say column already exists if it was already added

conn.commit()
conn.close()
