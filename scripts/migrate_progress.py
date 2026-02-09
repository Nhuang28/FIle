import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(__file__), '../app.db')

def migrate():
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(card_progress)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'repetitions' not in columns:
            print("Adding 'repetitions' column to 'card_progress' table...")
            cursor.execute("ALTER TABLE card_progress ADD COLUMN repetitions INTEGER DEFAULT 0")
            conn.commit()
            print("Migration successful: 'repetitions' column added.")
        else:
            print("'repetitions' column already exists.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
