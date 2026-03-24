import sys
import os

# Insert project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Deck, Class, ClassMember, StudyResult, CardProgress

app = create_app()

with app.app_context():
    email = "tomuk001134@gmail.com"
    user = User.query.filter_by(email=email).first()
    
    if user:
        print(f"Found user {user.email} with id {user.id}. Deleting associated information...")
        
        # Decks
        decks = Deck.query.filter_by(owner_id=user.id).all()
        for deck in decks:
            db.session.delete(deck)
            print(f"Deleted Deck: {deck.title}")
            
        # Classes Taught
        taught_classes = Class.query.filter_by(teacher_id=user.id).all()
        for cls in taught_classes:
            db.session.delete(cls)
            print(f"Deleted Class Taught: {cls.name}")
            
        # Classes Enrolled
        enrolled_classes = ClassMember.query.filter_by(student_id=user.id).all()
        for member in enrolled_classes:
            db.session.delete(member)
            print(f"Deleted Class Enrollment.")
            
        # Study Results
        results = StudyResult.query.filter_by(user_id=user.id).all()
        for result in results:
            db.session.delete(result)
            print(f"Deleted Study Result.")

        # Card Progress
        progress = CardProgress.query.filter_by(user_id=user.id).all()
        for p in progress:
            db.session.delete(p)
            print(f"Deleted Card Progress.")
            
        db.session.commit()
        print("Done deleting information.")
    else:
        print(f"User {email} not found in the database.")
