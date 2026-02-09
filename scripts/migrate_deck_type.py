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
        cursor.execute("PRAGMA table_info(decks)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'question_type' not in columns:
            print("Adding 'question_type' column to 'decks' table...")
            # Defaulting to 'flashcard' for existing decks
            cursor.execute("ALTER TABLE decks ADD COLUMN question_type TEXT NOT NULL DEFAULT 'flashcard'")
            conn.commit()
            print("Migration successful: 'question_type' column added.")
        else:
            print("'question_type' column already exists.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
