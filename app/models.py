from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('student', 'teacher'), nullable=False)
    last_active_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Deck(db.Model):
    __tablename__ = 'decks'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    visibility = db.Column(db.Enum('private', 'class'), default='private')
    question_type = db.Column(db.Enum('flashcard', 'fill_gap', 'mcq'), default='flashcard', nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    cards = db.relationship('Card', backref='deck', lazy='dynamic', cascade='all, delete-orphan')

class Card(db.Model):
    # This table stores all types of cards (flashcards, fill-in-the-gap, multiple choice)
    __tablename__ = 'cards'
    
    # Basic card information
    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=False)
    card_type = db.Column(db.Enum('flashcard', 'fill_gap', 'mcq'), nullable=False)
    
    # Columns for Flashcards
    front_text = db.Column(db.Text, nullable=True)
    back_text = db.Column(db.Text, nullable=True)
    cloze_template = db.Column(db.Text, nullable=True)
    
    # Columns for Fill in the Gap and Multiple Choice Questions
    question_text = db.Column(db.Text, nullable=True)
    
    # JSON columns to store lists of answers or options
    answers_json = db.Column(db.JSON, nullable=True)
    options_json = db.Column(db.JSON, nullable=True)
    
    # Specific columns for Multiple Choice Questions
    correct_index = db.Column(db.Integer, nullable=True)
    explanation_text = db.Column(db.Text, nullable=True)
    
    # Record when the card was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def answers(self):
        # Convert JSON string to Python list
        import json
        return json.loads(self.answers_json) if self.answers_json else []

    @property
    def options(self):
        # Convert JSON string to Python list
        import json
        return json.loads(self.options_json) if self.options_json else []

class CardProgress(db.Model):
    __tablename__ = 'card_progress'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), primary_key=True)
    next_review_date = db.Column(db.Date, nullable=True)
    ease_factor = db.Column(db.Numeric(4, 2), default=2.50)
    interval_days = db.Column(db.Integer, default=0)
    repetitions = db.Column(db.Integer, default=0)

class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    invite_code = db.Column(db.String(6), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    teacher = db.relationship('User', backref='taught_classes', foreign_keys=[teacher_id])
    members = db.relationship('ClassMember', backref='enrolled_class', lazy='dynamic', cascade='all, delete-orphan')

class ClassMember(db.Model):
    __tablename__ = 'class_members'
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('User', backref='enrolled_classes', foreign_keys=[student_id])

class StudyResult(db.Model):
    __tablename__ = 'study_results'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    max_score = db.Column(db.Integer, default=0)
    question_type = db.Column(db.String(50), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)


