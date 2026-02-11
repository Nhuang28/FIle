from app import create_app, db
from app.models import User, Deck, Card, CardProgress, Class, ClassMember
from datetime import datetime, date

app = create_app()

def seed(email):
    with app.app_context():
        # 1. Ensure Teacher Exists
        teacher_email = "teacher@gmail.com"
        teacher = User.query.filter_by(email=teacher_email).first()
        if not teacher:
            print(f"Creating teacher {teacher_email}...")
            teacher = User(email=teacher_email, role='teacher')
            teacher.set_password('password123')
            db.session.add(teacher)
            db.session.commit()
        else:
            print(f"Teacher {teacher.username} already exists. Resetting password...")
            teacher.set_password('password123')
            db.session.commit()

        # 2. Ensure Student Exists (The one passed in argument)
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"User {email} not found. Creating...")
            user = User(email=email, role='student')
            user.set_password('password123') # Default password if we need to create
            db.session.add(user)
            db.session.commit()
            print(f"User created with ID {user.id}")
        else:
            print(f"Checking data for user {user.username} (ID: {user.id})...")

        # Create Decks if empty
        if Deck.query.filter_by(owner_id=user.id).count() == 0:
            print("Creating sample decks...")
            deck1 = Deck(owner_id=user.id, title="Spanish Vocabulary", description="Common Spanish words for beginners.")
            deck2 = Deck(owner_id=user.id, title="Organic Chemistry", description="Functional groups and reactions.")
            
            db.session.add_all([deck1, deck2])
            db.session.commit()
            
            # Add Cards to Deck 1
            print("Adding cards...")
            cards = []
            for i in range(25): # 25 cards
                card = Card(deck_id=deck1.id, card_type='flashcard')
                cards.append(card)
                
            # Add Cards to Deck 2
            for i in range(15): # 15 cards
                card = Card(deck_id=deck2.id, card_type='flashcard')
                cards.append(card)
                
            db.session.add_all(cards)
            db.session.commit()
            
            # Create Progress (make 21 cards due for Spanish, 12 for Chemistry)
            # Due today means next_review_date <= today
            print("Creating progress entries...")
            today = date.today()
            progress_entries = []
            
            # Make 21 cards from Deck 1 due today
            deck1_cards = Card.query.filter_by(deck_id=deck1.id).limit(21).all()
            for card in deck1_cards:
                 p = CardProgress(user_id=user.id, card_id=card.id, next_review_date=today)
                 progress_entries.append(p)

            # Make 12 cards from Deck 2 due today
            deck2_cards = Card.query.filter_by(deck_id=deck2.id).limit(12).all()
            for card in deck2_cards:
                 p = CardProgress(user_id=user.id, card_id=card.id, next_review_date=today)
                 progress_entries.append(p)                 
                 
            db.session.add_all(progress_entries)
            db.session.commit()
            print("Seed data created successfully!")
        if Class.query.filter_by(teacher_id=teacher.id).count() == 0:
            print("Creating sample classes...")
            class1 = Class(teacher_id=teacher.id, name="AP World History", invite_code="HIST01")
            class2 = Class(teacher_id=teacher.id, name="Intro to Biology", invite_code="BIO101")
            class3 = Class(teacher_id=teacher.id, name="Calc BC - Section 4", invite_code="CALC04")
            class4 = Class(teacher_id=teacher.id, name="Spanish III Honors", invite_code="SPAN03")
            
            db.session.add_all([class1, class2, class3, class4])
            db.session.commit()
            print("Classes created.")
            
            # Enroll students in classes (mock data)
            # Enroll the student we just created/found above into these classes
            print(f"Enrolling {user.username} into classes...")
            member1 = ClassMember(class_id=class1.id, student_id=user.id)
            member2 = ClassMember(class_id=class2.id, student_id=user.id)
            db.session.add_all([member1, member2])
            db.session.commit()
        else:
            print("Classes already exist.")

        if Deck.query.filter_by(owner_id=user.id).count() != 0:
             print("Decks already exist. Skipping deck seed.")

if __name__ == '__main__':
    seed('tomuk001134@gmail.com')
