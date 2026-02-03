from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Class
import random
import string

bp = Blueprint('classes', __name__, url_prefix='/classes')

def generate_invite_code():
    """Generates a unique 6-character alphanumeric code."""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=6))
        if not Class.query.filter_by(invite_code=code).first():
            return code

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description') # Optional, if we add column later or just ignore
        
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
        
        flash(f'Class "{name}" created successfully! Invite code: {invite_code}', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('classes/create.html')
@bp.route('/join', methods=['GET', 'POST'])
@login_required
def join():
    if request.method == 'POST':
        invite_code = request.form.get('invite_code')
        if not invite_code:
            flash('Invite code is required.', 'error')
            return redirect(url_for('classes.join'))
            
        invite_code = invite_code.upper().strip()
        class_obj = Class.query.filter_by(invite_code=invite_code).first()
        
        if not class_obj:
            flash('Invalid invite code. Please check and try again.', 'error')
            return redirect(url_for('classes.join'))
            
        # Check if already a member
        from app.models import ClassMember
        if ClassMember.query.filter_by(class_id=class_obj.id, student_id=current_user.id).first():
            flash(f'You are already a member of "{class_obj.name}".', 'info')
            return redirect(url_for('classes.view', class_id=class_obj.id))
            
        # Add to class
        member = ClassMember(class_id=class_obj.id, student_id=current_user.id)
        db.session.add(member)
        db.session.commit()
        
        flash(f"Successfully joined '{class_obj.name}'!", 'success')
        return redirect(url_for('classes.view', class_id=class_obj.id))
        
    return render_template('classes/join.html')

@bp.route('/<int:class_id>')
@login_required
def view(class_id):
    class_obj = Class.query.get_or_404(class_id)
    
    # Optional: Check if user is member or teacher
    # if class_obj.teacher_id != current_user.id and not is_member: ...
    
    students = class_obj.members.all()
    
    return render_template('classes/view.html', class_=class_obj, students=students)
