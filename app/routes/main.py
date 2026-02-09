from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app import db
from app.models import Deck, CardProgress, Class
from datetime import date, datetime

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
    from app.models import StudyResult
    from sqlalchemy import func, and_
    import calendar

    # Get filter parameters from query string
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')

    today = date.today()
    
    # Default: Jan 1st of current year to Today
    if start_str:
        try:
            start_date = datetime.strptime(start_str, '%Y-%m').date().replace(day=1)
        except ValueError:
            start_date = date(today.year, 1, 1)
    else:
        start_date = date(today.year, 1, 1)

    if end_str:
        try:
            # End of selected month
            end_dt = datetime.strptime(end_str, '%Y-%m')
            # Get last day of month
            last_day = calendar.monthrange(end_dt.year, end_dt.month)[1]
            end_date = end_dt.date().replace(day=last_day)
        except ValueError:
            end_date = today
    else:
        end_date = today

    # Base query for user's results within range
    # Filter out 'flashcard' type if Points strictly means "Correct Answer"
    # But usually flashcards don't have scores like MCQ. 
    # The requirement says: 1 Correct Answer (MCQ/Gap) = 1 Point. 
    # Flashcards in our seed script might have scores, but user prompt implied logic:
    # "Ensuring the Y-axis accurately reflects the percentage of correct MCQ and Fill-in-the-gap questions out of the total attempted questions (excluding Flashcards)."
    
    base_query = StudyResult.query.filter(
        StudyResult.user_id == current_user.id,
        StudyResult.completed_at >= start_date,
        StudyResult.completed_at <= datetime.combine(end_date, datetime.max.time()),
        StudyResult.question_type.in_(['mcq', 'fill_gap']) 
    )

    results = base_query.all()
    
    attempted_questions = len(results)
    
    # Calculate Total Points (assuming score is 1 for correct, or sum of scores if score tracked)
    # The user request said: "logic where each correct answer... counts as 1 point". 
    # Our StudyResult has 'score' and 'max_score'. 
    # If score > 0 it's likely correct? Or if score == max_score?
    # Let's assume for now score is the points. 
    # BUT, specific logic requested earlier: "Points must be <= Attempted questions".
    # So max score for a single question should be 1. 
    # Our seed script generates scores like 5-20. We need to normalize or count "correct" ones.
    # Let's assume ANY score > 0 is "Correct" = 1 Point? 
    # OR better: (score / max_score) * 1. 
    # Let's go with: Points = Sum(score) but capped?
    # Re-reading prompt: "implement a logic where each correct answer ... counts as 1 point".
    # So if I got 5/5 on a question, that's 1 point. If I got 0/5, 0 points.
    
    total_points = 0
    for r in results:
        if r.max_score > 0 and (r.score / r.max_score) >= 0.5: # Threshold for "correct"
            total_points += 1
            
    # Accuracy
    accuracy = 0
    if attempted_questions > 0:
        accuracy = int((total_points / attempted_questions) * 100)
    
    # Monthly Data for Chart
    # We need a list of accuracies for every month in the range. 
    
    monthly_data = [] # List of dicts or just values? Template expects list of values.
    # But if range is 13 months, list needs 13 items.
    # And we need labels (Jan, Feb...).
    
    current_m = start_date.replace(day=1)
    month_labels = []
    monthly_accuracy = []
    
    while current_m <= end_date:
        # End of this month
        last_day = calendar.monthrange(current_m.year, current_m.month)[1]
        m_end = current_m.replace(day=last_day)
        
        # Query for this specific month
        m_results = [r for r in results if r.completed_at.date() >= current_m and r.completed_at.date() <= m_end]
        
        m_attempts = len(m_results)
        m_points = 0
        for r in m_results:
             if r.max_score > 0 and (r.score / r.max_score) >= 0.5:
                m_points += 1
        
        if m_attempts > 0:
            m_acc = int((m_points / m_attempts) * 100)
        else:
            m_acc = 0
            
        monthly_accuracy.append(m_acc)
        month_labels.append(current_m.strftime("%b %y")) # e.g., Jan 25
        
        # Next month
        if current_m.month == 12:
            current_m = current_m.replace(year=current_m.year + 1, month=1)
        else:
            current_m = current_m.replace(month=current_m.month + 1)
            
    return render_template('stats.html',
                           total_points=total_points,
                           attempted_questions=attempted_questions,
                           accuracy=accuracy,
                           monthly_accuracy=monthly_accuracy,
                           month_labels=month_labels,
                           start_date=start_str or start_date.strftime('%Y-%m'),
                           end_date=end_str or end_date.strftime('%Y-%m'))

