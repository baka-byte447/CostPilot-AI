import sqlite3
import os
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH

def clear_database():
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found.")
        return

    print(f"Clearing database at {DB_PATH}...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
        
        for table in tables:
            print(f"Truncating table: {table}")
            cursor.execute(f"DELETE FROM {table}")
            # Reset auto-increment
            try:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
            except sqlite3.OperationalError:
                pass
        
        conn.commit()
        conn.close()
        print("Database cleared successfully.")
    except Exception as e:
        print(f"Error clearing database: {e}")

if __name__ == "__main__":
    clear_database()
