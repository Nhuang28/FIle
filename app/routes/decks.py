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
        visibility = request.form.get('visibility', 'private')
        
        if not title:
            flash('Deck title is required.', 'error')
            return redirect(url_for('decks.create'))
            
        deck = Deck(
            owner_id=current_user.id,
            title=title,
            description=description,
            visibility=visibility
        )
        
        db.session.add(deck)
        db.session.commit()
        
        flash(f'Deck "{title}" created successfully!', 'success')
        # In the future, this might redirect to 'add cards' wizard
        return redirect(url_for('main.dashboard'))
        
    return render_template('decks/create.html')
