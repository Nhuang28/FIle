from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Class, Deck, User, ClassMember, Card, CardProgress
from datetime import datetime
import string
import random

bp = Blueprint('classes', __name__, url_prefix='/classes')

def generate_invite_code():
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=6))
        if not Class.query.filter_by(invite_code=code).first():
            return code

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if current_user.role != 'teacher':
        flash('Only teachers can create classes.', 'error')
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash('Class name is required.', 'error')
            return redirect(url_for('classes.create'))
            
        invite_code = generate_invite_code()
        new_class = Class(
            teacher_id=current_user.id,
            name=name,
            invite_code=invite_code
        )
        db.session.add(new_class)
        db.session.commit()
        
        # Determine previous page or dashboard
        # For now redirect to dashboard or class view
        flash('Class created successfully!', 'success')
        # We might want to separate 'success' page from pure redirect, 
        # but for now let's redirect to dashboard or view
        return redirect(url_for('classes.view', class_id=new_class.id))
        
    return render_template('classes/create.html')

@bp.route('/<int:class_id>')
@login_required
def view(class_id):
    # Check access: Teacher owner or Student member
    class_obj = Class.query.get_or_404(class_id)
    
    is_teacher = (current_user.id == class_obj.teacher_id)
    is_member = False
    
    if current_user.role == 'student':
        membership = ClassMember.query.filter_by(student_id=current_user.id, class_id=class_id).first()
        if membership:
            is_member = True
            
    if not is_teacher and not is_member:
        flash('You do not have access to this class.', 'error')
        return redirect(url_for('main.dashboard'))
        
    # Get decks for this class
    decks = Deck.query.filter_by(class_id=class_id).all()

    if current_user.role == 'student':
        deck_progress = {}
        for deck in decks:
            total_cards = deck.cards.count()
            if total_cards > 0:
                # Count valid progress entries (e.g. reviewed at least once or based on some progress metric)
                # Here assuming any existence in CardProgress implies "started/learning"
                # If "complete" means mastered, we should filter by mastery_level.
                # User request said "thống kê hoàn thành" (completion stats). 
                # Let's count cards that have progress:
                learned_count = CardProgress.query.join(Card).filter(
                    Card.deck_id == deck.id,
                    CardProgress.user_id == current_user.id
                ).count()
                progress_percent = int((learned_count / total_cards) * 100)
                deck_progress[deck.id] = progress_percent
            else:
                deck_progress[deck.id] = 0
                
        return render_template('classes/student_view.html',
                               class_obj=class_obj,
                               decks=decks,
                               deck_progress=deck_progress)
    
    return render_template('classes/view.html', 
                           class_obj=class_obj, 
                           decks=decks, 
                           is_teacher=is_teacher)

@bp.route('/join', methods=['GET', 'POST'])
@login_required
def join():
    if request.method == 'POST':
        invite_code = request.form.get('invite_code')
        if not invite_code:
            flash('Please enter an invite code.', 'error')
            return redirect(url_for('classes.join'))
            
        # Find class
        class_obj = Class.query.filter_by(invite_code=invite_code).first()
        if not class_obj:
            flash('Invalid invite code.', 'error')
            return redirect(url_for('classes.join'))
            
        # Check if already a member
        if ClassMember.query.filter_by(student_id=current_user.id, class_id=class_obj.id).first():
            flash(f'You are already a member of {class_obj.name}.', 'info')
            return redirect(url_for('classes.view', class_id=class_obj.id))
            
        # Add to class
        membership = ClassMember(student_id=current_user.id, class_id=class_obj.id)
        db.session.add(membership)
        db.session.commit()
        
        flash(f'Successfully joined {class_obj.name}!', 'success')
        return redirect(url_for('classes.view', class_id=class_obj.id))
        
    return render_template('classes/join.html')

@bp.route('/<int:class_id>/delete', methods=['POST'])
@login_required
def delete(class_id):
    class_obj = Class.query.get_or_404(class_id)
    if class_obj.teacher_id != current_user.id:
        flash('You do not have permission to delete this class.', 'error')
        return redirect(url_for('classes.view', class_id=class_obj.id))
        
    try:
        db.session.delete(class_obj)
        db.session.commit()
        flash('Class deleted successfully.', 'success')
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting class: {str(e)}', 'error')
        return redirect(url_for('classes.view', class_id=class_obj.id))
