import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(__file__), '../app.db')

def migrate():
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='study_results'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("Creating 'study_results' table...")
            cursor.execute("""
                CREATE TABLE study_results (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    deck_id INTEGER NOT NULL,
                    score INTEGER DEFAULT 0,
                    max_score INTEGER DEFAULT 0,
                    question_type VARCHAR(50) NOT NULL,
                    completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(deck_id) REFERENCES decks(id)
                )
            """)
            conn.commit()
            print("Migration successful: 'study_results' table created.")
        else:
            print("'study_results' table already exists.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
