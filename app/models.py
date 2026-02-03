from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
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
        return f'<User {self.username}>'

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
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    cards = db.relationship('Card', backref='deck', lazy='dynamic', cascade='all, delete-orphan')

class Card(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=False)
    card_type = db.Column(db.Enum('flashcard', 'fill_gap', 'mcq'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships to subtypes are handled via backrefs in subtype models below

class CardFlashcard(db.Model):
    __tablename__ = 'card_flashcard'
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), primary_key=True)
    front_text = db.Column(db.Text, nullable=True)
    back_text = db.Column(db.Text, nullable=True)
    cloze_template = db.Column(db.Text, nullable=True)
    answers_json = db.Column(db.JSON, nullable=True)
    
    card = db.relationship('Card', backref=db.backref('flashcard', uselist=False, cascade='all, delete-orphan'))

class CardFillGap(db.Model):
    __tablename__ = 'card_fill_gap'
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    answers_json = db.Column(db.JSON, nullable=False)
    
    card = db.relationship('Card', backref=db.backref('fill_gap', uselist=False, cascade='all, delete-orphan'))

class CardMCQ(db.Model):
    __tablename__ = 'card_mcq'
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    options_json = db.Column(db.JSON, nullable=False)
    correct_index = db.Column(db.Integer, nullable=False)
    explanation_text = db.Column(db.Text, nullable=True)
    
    card = db.relationship('Card', backref=db.backref('mcq', uselist=False, cascade='all, delete-orphan'))

class CardProgress(db.Model):
    __tablename__ = 'card_progress'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id'), primary_key=True)
    next_review_date = db.Column(db.Date, nullable=True)
    ease_factor = db.Column(db.Numeric(4, 2), default=2.50)
    interval_days = db.Column(db.Integer, default=0)

class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    invite_code = db.Column(db.String(6), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher = db.relationship('User', backref='taught_classes', foreign_keys=[teacher_id])
    members = db.relationship('ClassMember', backref='enrolled_class', lazy='dynamic', cascade='all, delete-orphan')

class ClassMember(db.Model):
    __tablename__ = 'class_members'
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to Student (User)
    student = db.relationship('User', backref='enrolled_classes', foreign_keys=[student_id])


