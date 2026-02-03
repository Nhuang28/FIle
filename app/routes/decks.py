from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Deck
from datetime import datetime

bp = Blueprint('decks', __name__, url_prefix='/decks')

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        visibility = request.form.get('visibility')
        class_id = request.form.get('class_id')
        
        # Enforce Private for Students
        if current_user.role == 'student':
            visibility = 'private'
            class_id = None
        
        # Basic validation
        if not title:
            flash('Deck title is required', 'error')
            return redirect(url_for('decks.create'))
            
        # If visibility is class, class_id is required
        if visibility == 'class' and not class_id:
             flash('Please select a class for class visibility', 'error')
             return redirect(url_for('decks.create'))
        
        # Sanitize class_id to Integer or None
        final_class_id = int(class_id) if (visibility == 'class' and class_id) else None

        deck = Deck(
            owner_id=current_user.id,
            title=title,
            description=description,
            visibility=visibility,
            class_id=final_class_id
        )
        
        db.session.add(deck)
        db.session.commit()
        
        flash('Deck created successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    # Check for Teacher or Student to fetch relevant classes
    from app.models import Class, ClassMember
    classes_list = []
    if current_user.role == 'teacher':
        classes_list = Class.query.filter_by(teacher_id=current_user.id).all()
    else:
        # Join ClassMember to find classes user has joined
        classes_list = Class.query.join(ClassMember).filter(ClassMember.student_id == current_user.id).all()
        
    return render_template('decks/create.html', classes=classes_list)

@bp.route('/list')
@login_required
def list():
    # Private Decks
    private_decks = Deck.query.filter_by(owner_id=current_user.id, visibility='private').all()
    
    # Class Decks
    class_decks = []
    if current_user.role == 'student':
        # Get decks from classes user has joined
        # This relationship might need checking if 'enrolled_classes' returns ClassMember objects or Class objects
        # Based on models.py: student = db.relationship('User', backref='enrolled_classes', ...) in ClassMember
        # So current_user.enrolled_classes is a list of ClassMember objects
        joined_class_ids = [m.class_id for m in current_user.enrolled_classes]
        if joined_class_ids:
            class_decks = Deck.query.filter(Deck.visibility == 'class', Deck.class_id.in_(joined_class_ids)).all()
    else:
        # For teacher, show decks from classes they own? Or just their own decks?
        # User request focused on student. For now, let's show class decks they created.
        class_decks = Deck.query.filter_by(owner_id=current_user.id, visibility='class').all()

    return render_template('decks/list.html', private_decks=private_decks, class_decks=class_decks)
