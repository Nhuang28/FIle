import sys
import os
from datetime import datetime, timedelta, date
import random
from app import create_app, db
from app.models import User, Deck, StudyResult

# Add the project root to the python path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = create_app()

def seed_stats(email):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"User with email {email} not found.")
            return

        print(f"Seeding stats for user: {user.username} ({user.email})")

        # Get some decks to assign results to
        decks = Deck.query.all()
        if not decks:
            print("No decks found in database. Please create some decks first.")
            return
        
        # Date range: Jan 1, 2025 to Jan 31, 2026
        start_date = date(2025, 1, 1)
        end_date = date(2026, 1, 31)
        
        current_date = start_date
        records_created = 0

        while current_date <= end_date:
            # Randomly decide if the user studied on this day (e.g., 70% chance)
            if random.random() < 0.7:
                # Random number of sessions per day (1 to 5)
                num_sessions = random.randint(1, 5)
                
                for _ in range(num_sessions):
                    deck = random.choice(decks)
                    max_score = random.randint(5, 20) # Mock max score
                    # Score is usually somewhat high, but varies
                    score = int(max_score * random.uniform(0.5, 1.0))
                    
                    question_type = random.choice(['mcq', 'fill_gap', 'flashcard'])
                    
                    # Create datetime from date + random time
                    completed_at = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=random.randint(8, 22), minutes=random.randint(0, 59))

                    result = StudyResult(
                        user_id=user.id,
                        deck_id=deck.id,
                        score=score,
                        max_score=max_score,
                        question_type=question_type,
                        completed_at=completed_at
                    )
                    db.session.add(result)
                    records_created += 1
            
            current_date += timedelta(days=1)
        
        db.session.commit()
        print(f"Successfully created {records_created} study result records.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = "tomuk001134@gmail.com" # Default as requested
    
    seed_stats(email)
