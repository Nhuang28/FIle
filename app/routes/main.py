from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Deck, CardProgress, Class
from datetime import date

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'teacher':
        classes = Class.query.filter_by(teacher_id=current_user.id).all()
        # Calculate stats
        total_students = sum([c.members.count() for c in classes])
        avg_mastery = 84 # Mock data for now
        
        return render_template('dashboard/teacher.html',
                               classes=classes,
                               total_students=total_students,
                               avg_mastery=avg_mastery)
    
    # Students
    decks = Deck.query.filter_by(owner_id=current_user.id).all()
    
    # Calculate cards due today
    today = date.today()
    cards_due_count = CardProgress.query.filter(
        CardProgress.user_id == current_user.id,
        CardProgress.next_review_date <= today
    ).count()
    
    # Mock data for stats (could be real if we implemented ReviewLogs)
    stats = {
        'accuracy': 88,
        'streak_days': 15,
        'reviewed_count': 450,
        'study_minutes': 32
    }
    
    return render_template('dashboard/student.html', 
                           decks=decks, 
                           cards_due_count=cards_due_count,
                           stats=stats)
