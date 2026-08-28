import sqlite3

# Aapka database path
conn = sqlite3.connect("attendance.db")  # Jo bhi aapki DB_PATH file ka naam hai
cur = conn.cursor()

# Table ke columns check karein
cur.execute("PRAGMA table_info(students);")
columns = cur.fetchall()

print("Columns in students table:")
for col in columns:
    print(f"- {col[1]} ({col[2]})")

conn.close()