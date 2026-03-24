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
        
        return render_template('dashboard/teacher.html',
                               classes=classes)
    
    decks = Deck.query.filter_by(owner_id=current_user.id).all()
    
    today = date.today()
    cards_due_count = CardProgress.query.filter(
        CardProgress.user_id == current_user.id,
        CardProgress.next_review_date <= today
    ).count()
    
    stats = {
        'accuracy': 88,
        'streak_days': 15,
        'reviewed_count': 450,
        'study_minutes': 32
    }
    
    enrolled_classes = current_user.enrolled_classes
    
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

    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')

    today = date.today()
    
    if start_str:
        try:
            start_date = datetime.strptime(start_str, '%Y-%m').date().replace(day=1)
        except ValueError:
            start_date = date(today.year, 1, 1)
    else:
        start_date = date(today.year, 1, 1)

    if end_str:
        try:
            end_dt = datetime.strptime(end_str, '%Y-%m')
            last_day = calendar.monthrange(end_dt.year, end_dt.month)[1]
            end_date = end_dt.date().replace(day=last_day)
        except ValueError:
            end_date = today
    else:
        end_date = today

    
    base_query = StudyResult.query.filter(
        StudyResult.user_id == current_user.id,
        StudyResult.completed_at >= start_date,
        StudyResult.completed_at <= datetime.combine(end_date, datetime.max.time()),
        StudyResult.question_type.in_(['mcq', 'fill_gap']) 
    )

    results = base_query.all()
    
    attempted_questions = len(results)
    
    
    total_points = 0
    for r in results:
        if r.max_score > 0 and (r.score / r.max_score) >= 0.5:
            total_points += 1
            
    accuracy = 0
    if attempted_questions > 0:
        accuracy = int((total_points / attempted_questions) * 100)
    
    
    monthly_data = []
    
    current_m = start_date.replace(day=1)
    month_labels = []
    monthly_accuracy = []
    
    while current_m <= end_date:
        last_day = calendar.monthrange(current_m.year, current_m.month)[1]
        m_end = current_m.replace(day=last_day)
        
        # Filter results that fall within the current month
        m_results = []
        for r in results:
            if r.completed_at.date() >= current_m and r.completed_at.date() <= m_end:
                m_results.append(r)
        
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
        month_labels.append(current_m.strftime("%b %y"))
        
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

