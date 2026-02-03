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
    
    # Get enrolled classes
    enrolled_classes = current_user.enrolled_classes # List of ClassMember objects
    
    return render_template('dashboard/student.html', 
                           decks=decks, 
                           cards_due_count=cards_due_count,
                           stats=stats,
                           enrolled_classes=enrolled_classes)

@bp.route('/stats')
@login_required
def stats():
    # Mock Data Logic as requested
    # Formula concept: (Correct MCQ + Correct Fill-in-gap) / (Total attempted excluding Flashcards)
    
    # Mock Monthly Accuracies for 2026 (12 months)
    # Trends showing improvement over the year
    monthly_accuracy = [65, 68, 72, 70, 75, 78, 82, 80, 85, 88, 90, 92]
    
    # Mock Aggregates (Year to Date)
    # Logic: 1 Correct Answer (MCQ/Gap) = 1 Point
    # Therefore, Points must be <= Attempted Questions
    attempted_questions = 320 # MCQ + Fill-in-gap attempts
    
    # Calculate average accuracy from the monthly data for consistency
    if monthly_accuracy:
        accuracy = int(sum(monthly_accuracy) / len(monthly_accuracy))
    else:
        accuracy = 0
        
    # Calculate points based on accuracy (approximately) to satisfy Points <= Attempts
    # Points = Attempts * Accuracy%
    total_points = int(attempted_questions * (accuracy / 100))
    
    return render_template('stats.html',
                           total_points=total_points,
                           attempted_questions=attempted_questions,
                           accuracy=accuracy,
                           monthly_accuracy=monthly_accuracy)
