from app import create_app, db
from app.models import User, Class, Deck, Card, CardFlashcard, CardFillGap, CardMCQ
import json

app = create_app()

def seed():
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        # 1. Find or Create Teacher
        teacher = User.query.filter_by(role='teacher').first()
        if not teacher:
            print("No teacher found. Creating one...")
            teacher = User(email='teacher@bio.com', role='teacher')
            teacher.set_password('password123')
            db.session.add(teacher)
            db.session.commit()
        
        print(f"Using teacher: {teacher.username}")

        # 2. Find or Create Class
        class_name = 'Intro to Biology'
        bio_class = Class.query.filter_by(name=class_name, teacher_id=teacher.id).first()
        if not bio_class:
            print(f"Creating class: {class_name}")
            # Generate unique invite code
            import random, string
            chars = string.ascii_uppercase + string.digits
            invite_code = ''.join(random.choices(chars, k=6))
            
            bio_class = Class(name=class_name, teacher_id=teacher.id, invite_code=invite_code)
            db.session.add(bio_class)
            db.session.commit()
        else:
            print(f"Class exists: {class_name}")

        # 3. Create Decks
        deck_titles = ["Cell Structure", "Genetics Basics", "Evolutionary Biology"]
        created_decks = []
        
        for title in deck_titles:
            deck = Deck.query.filter_by(title=title, class_id=bio_class.id).first()
            if not deck:
                print(f"Creating deck: {title}")
                deck = Deck(
                    title=title,
                    description=f"Learn about {title.lower()}.",
                    visibility='class',
                    class_id=bio_class.id,
                    owner_id=teacher.id
                )
                db.session.add(deck)
                db.session.commit()
            created_decks.append(deck)

        # 4. Insert Cards into the first deck ("Cell Structure")
        target_deck = created_decks[0]
        print(f"Adding cards to deck: {target_deck.title}")

        # Card 1: Flashcard
        if not Card.query.filter_by(deck_id=target_deck.id, card_type='flashcard').first():
            print("- Adding Flashcard")
            card1 = Card(deck_id=target_deck.id, card_type='flashcard')
            db.session.add(card1)
            db.session.flush() # Get ID
            
            flashcard = CardFlashcard(
                card_id=card1.id,
                front_text="What is the function of the Mitochondria?",
                back_text="It produces energy for the cell (Powerhouse)."
            )
            db.session.add(flashcard)

        # Card 2: Fill in the gap
        if not Card.query.filter_by(deck_id=target_deck.id, card_type='fill_gap').first():
            print("- Adding Fill in the Gap")
            card2 = Card(deck_id=target_deck.id, card_type='fill_gap')
            db.session.add(card2)
            db.session.flush()
            
            fillgap = CardFillGap(
                card_id=card2.id,
                question_text="The _____ stores the cell's DNA.",
                answers_json=["Nucleus"] # JSON list implicitly handled if using db.JSON, else might need json.dumps
            )
            db.session.add(fillgap)
        
        # Card 3: MCQ
        if not Card.query.filter_by(deck_id=target_deck.id, card_type='mcq').first():
            print("- Adding MCQ")
            card3 = Card(deck_id=target_deck.id, card_type='mcq')
            db.session.add(card3)
            db.session.flush()
            
            mcq = CardMCQ(
                card_id=card3.id,
                question_text="Which of the following is NOT a type of cell division?",
                options_json=["Mitosis", "Meiosis", "Photosynthesis", "Binary Fission"],
                correct_index=2, # Photosynthesis
                explanation_text="Photosynthesis is a process used by plants to make food, not cell division."
            )
            db.session.add(mcq)

        db.session.commit()
        print("Data generation complete!")

if __name__ == "__main__":
    seed()
