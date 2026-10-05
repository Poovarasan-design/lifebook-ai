import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "lifebook.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(users);")
cols = [col[1] for col in cursor.fetchall()]
print("Current columns in users:", cols)

if "google_id" not in cols:
    cursor.execute("ALTER TABLE users ADD COLUMN google_id VARCHAR(255);")
    print("Added google_id")

if "avatar_url" not in cols:
    cursor.execute("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(512);")
    print("Added avatar_url")

if "auth_provider" not in cols:
    cursor.execute("ALTER TABLE users ADD COLUMN auth_provider VARCHAR(50) DEFAULT 'local';")
    print("Added auth_provider")

conn.commit()
cursor.execute("PRAGMA table_info(users);")
print("Updated columns in users:", [col[1] for col in cursor.fetchall()])
conn.close()
print("Migration finished successfully.")
