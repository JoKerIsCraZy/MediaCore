import sqlite3
import os

# Calculate absolute path to the DB
base_dir = os.getcwd() # Should be backend/
target_db_path = os.path.abspath(os.path.join(base_dir, "../api-central/media_database.db"))

print(f"CWD: {base_dir}")
print(f"Target DB: {target_db_path}")

if not os.path.exists(target_db_path):
    print("❌ FILE DOES NOT EXIST")
else:
    print(f"✅ File exists, size: {os.path.getsize(target_db_path)}")

try:
    conn = sqlite3.connect(target_db_path)
    cursor = conn.cursor()
    
    print("\n--- Tables ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for t in tables:
        print(f"- {t[0]}")
        
    if ('movies',) in tables:
        print("\n--- Counting movies ---")
        cursor.execute("SELECT count(*) FROM movies")
        count = cursor.fetchone()[0]
        print(f"Count: {count}")
        
        print("\n--- Sample Movie ---")
        cursor.execute("SELECT * FROM movies LIMIT 1")
        col_names = [description[0] for description in cursor.description]
        print(f"Columns: {col_names}")
        print(f"Row: {cursor.fetchone()}")
        
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
