from flask import Blueprint, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Card

bp = Blueprint('cards', __name__, url_prefix='/cards')

@bp.route('/<int:card_id>/delete', methods=['POST'])
@login_required
def delete(card_id):
    card = Card.query.get_or_404(card_id)
    deck = card.deck
    
    # Check permission (must own the deck)
    if deck.owner_id != current_user.id:
        flash('You do not have permission to delete this card.', 'error')
        return redirect(url_for('decks.view', deck_id=deck.id))
        
    try:
        db.session.delete(card)
        db.session.commit()
        flash('Card deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting card: {str(e)}', 'error')
        
    return redirect(url_for('decks.view', deck_id=deck.id))

@bp.route('/<int:card_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(card_id):
    from flask import render_template, request
    import json
    
    card = Card.query.get_or_404(card_id)
    deck = card.deck
    
    # Check permission
    if deck.owner_id != current_user.id:
        flash('You do not have permission to edit this card.', 'error')
        return redirect(url_for('decks.view', deck_id=deck.id))
        
    if request.method == 'POST':
        try:
            if card.card_type == 'mcq':
                question = request.form.get('question')
                opt0 = request.form.get('option_0')
                opt1 = request.form.get('option_1')
                opt2 = request.form.get('option_2')
                opt3 = request.form.get('option_3')
                correct_idx = request.form.get('correct_index')
                explanation = request.form.get('explanation')
                
                if not question or not all([opt0, opt1, opt2, opt3]) or correct_idx is None:
                    raise ValueError("All fields are required")
                    
                card.mcq.question_text = question
                card.mcq.options_json = json.dumps([opt0, opt1, opt2, opt3])
                card.mcq.correct_index = int(correct_idx)
                card.mcq.explanation_text = explanation
                
            elif card.card_type == 'flashcard':
                front = request.form.get('front')
                back = request.form.get('back')
                
                if not front or not back:
                     raise ValueError("Front and Back text are required")
                     
                card.flashcard.front_text = front
                card.flashcard.back_text = back
                
            elif card.card_type == 'fill_gap':
                question_text = request.form.get('question_text')
                answer = request.form.get('answer')
                
                if not question_text or not answer:
                    raise ValueError("Sentence and hidden word are required")
                    
                card.fill_gap.question_text = question_text
                card.fill_gap.answers_json = json.dumps([answer])

            db.session.commit()
            flash('Card updated successfully!', 'success')
            return redirect(url_for('decks.view', deck_id=deck.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating card: {str(e)}', 'error')
            
    return render_template('cards/edit.html', card=card)
