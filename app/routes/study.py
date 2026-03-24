from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Deck, StudyResult
from datetime import datetime
import json

bp = Blueprint('study', __name__, url_prefix='/study')

@bp.route('/session/<int:deck_id>')
@login_required
def session(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    
    has_access = False
    if deck.owner_id == current_user.id:
        has_access = True
    elif deck.visibility == 'class' and deck.class_id:
        # Check if the student is in the class this deck belongs to
        for member in current_user.enrolled_classes:
            if member.class_id == deck.class_id:
                has_access = True
                break
            
    if not has_access:
        return redirect(url_for('decks.list'))

    cards_data = []
    
    cards_list = deck.cards.all()
    
    if not cards_list:
        return render_template('study/session.html', deck=deck, cards_json='[]')

    for card in cards_list:
        try:
            # Create a dictionary to hold the card's data for the frontend
            card_obj = {
                'id': card.id,
                'type': str(card.card_type)
            }
            
            # Add fields based on the type of card
            if card.card_type == 'flashcard':
                card_obj['front'] = str(card.front_text or '')
                card_obj['back'] = str(card.back_text or '')

            elif card.card_type == 'fill_gap':
                card_obj['sentence'] = str(card.question_text or '')
                
                # Get the answers from the database safely
                try:
                    # In python, card.answers returns a list if answers_json is valid
                    raw_answers = card.answers
                    
                    # Ensure all answers are converted to strings
                    string_answers = []
                    if isinstance(raw_answers, list):
                        for a in raw_answers:
                            string_answers.append(str(a))
                    card_obj['answers'] = string_answers
                except Exception:
                    card_obj['answers'] = []

            elif card.card_type == 'mcq':
                card_obj['question'] = str(card.question_text or '')
                
                # Get options from the database safely
                try:
                    raw_options = card.options
                    
                    # Convert all options to strings
                    string_options = []
                    if isinstance(raw_options, list):
                        for o in raw_options:
                            string_options.append(str(o))
                    card_obj['options'] = string_options
                except Exception:
                    card_obj['options'] = []
                    
                card_obj['correct_index'] = int(card.correct_index) if card.correct_index is not None else 0
                card_obj['explanation'] = str(card.explanation_text or 'None')
                
            # Add the mapped card object to our final list mapping
            cards_data.append(card_obj)
        except Exception as e:
            continue
        
    return render_template('study/session.html', deck=deck, cards_data=cards_data)

@bp.route('/save_result', methods=['POST'])
@login_required
def save_result():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    try:
        result = StudyResult(
            user_id=current_user.id,
            deck_id=data.get('deck_id'),
            score=data.get('score'),
            max_score=data.get('max_score'),
            question_type=data.get('question_type'),
            completed_at=datetime.utcnow()
        )
        db.session.add(result)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/save_progress', methods=['POST'])
@login_required
def save_progress():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    card_id = data.get('card_id')
    quality = data.get('quality')
    
    if card_id is None or quality is None:
         return jsonify({'error': 'Missing card_id or quality'}), 400

    try:
        from app.models import CardProgress, Card
        from datetime import timedelta, date
        
        progress = CardProgress.query.get((current_user.id, card_id))
        if not progress:
            progress = CardProgress(user_id=current_user.id, card_id=card_id)
            db.session.add(progress)
            
        
        if quality < 3:
            progress.repetitions = 0
            progress.interval_days = 1
        else:
            if progress.repetitions == 0:
                progress.interval_days = 1
            elif progress.repetitions == 1:
                progress.interval_days = 6
            else:
                progress.interval_days = int(progress.interval_days * float(progress.ease_factor))
            
            progress.repetitions += 1
            
        new_ef = float(progress.ease_factor) + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if new_ef < 1.3:
            new_ef = 1.3
        progress.ease_factor = new_ef
        
        progress.next_review_date = date.today() + timedelta(days=progress.interval_days)
        
        db.session.commit()
        return jsonify({'success': True, 'next_review': progress.next_review_date.isoformat()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
