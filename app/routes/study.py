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
    
    # Permission check (can be refactored into a decorator or helper)
    has_access = False
    if deck.owner_id == current_user.id:
        has_access = True
    elif deck.visibility == 'class' and deck.class_id:
        if any(m.class_id == deck.class_id for m in current_user.enrolled_classes):
            has_access = True
            
    if not has_access:
        return redirect(url_for('decks.list'))

    # Prepare cards data for JS
    cards_data = []
    
    # Iterate through deck.cards (dynamic relationship)
    cards_list = deck.cards.all()
    
    if not cards_list:
        # Empty deck
        return render_template('study/session.html', deck=deck, cards_json='[]')

    for card in cards_list:
        try:
            # Base card object (PURE DICTIONARY)
            card_obj = {
                'id': card.id,
                'type': str(card.card_type) # Ensure string
            }
            
            if card.card_type == 'flashcard':
                if card.flashcard:
                    card_obj['front'] = str(card.flashcard.front_text or '')
                    card_obj['back'] = str(card.flashcard.back_text or '')
                else:
                    continue

            elif card.card_type == 'fill_gap':
                if card.fill_gap:
                    card_obj['sentence'] = str(card.fill_gap.question_text or '')
                    try:
                        # Ensure answers is a LIST of STRINGS
                        raw_answers = json.loads(card.fill_gap.answers_json) if card.fill_gap.answers_json else []
                        if isinstance(raw_answers, list):
                             card_obj['answers'] = [str(a) for a in raw_answers]
                        else:
                             card_obj['answers'] = []
                    except (json.JSONDecodeError, TypeError):
                        card_obj['answers'] = []
                else:
                    continue

            elif card.card_type == 'mcq':
                if card.mcq:
                    card_obj['question'] = str(card.mcq.question_text or '')
                    try:
                        # Ensure options is a LIST of STRINGS
                        raw_options = json.loads(card.mcq.options_json) if card.mcq.options_json else []
                        if isinstance(raw_options, list):
                            card_obj['options'] = [str(o) for o in raw_options]
                        else:
                            card_obj['options'] = []
                    except (json.JSONDecodeError, TypeError):
                        card_obj['options'] = []
                        
                    card_obj['correct_index'] = int(card.mcq.correct_index) if card.mcq.correct_index is not None else 0
                    card_obj['explanation'] = str(card.mcq.explanation_text or 'None')
                else:
                    continue
                
            cards_data.append(card_obj)
        except Exception as e:
            print(f"Error processing card ID {card.id}: {e}")
            continue
        
    # Pass the list of dicts directly, let Jinja tojson handle it
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
    quality = data.get('quality') # 0-5
    
    if card_id is None or quality is None:
         return jsonify({'error': 'Missing card_id or quality'}), 400

    try:
        from app.models import CardProgress, Card
        from datetime import timedelta, date
        
        # Get or create progress
        progress = CardProgress.query.get((current_user.id, card_id))
        if not progress:
            progress = CardProgress(user_id=current_user.id, card_id=card_id)
            db.session.add(progress)
            
        # SM-2 Algorithm
        # Quality: 0=Again, 3=Medium, 4=Easy, 5=Remember
        
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
            
        # Update EF
        # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = float(progress.ease_factor) + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if new_ef < 1.3:
            new_ef = 1.3
        progress.ease_factor = new_ef
        
        # Update Next Review Date
        progress.next_review_date = date.today() + timedelta(days=progress.interval_days)
        
        db.session.commit()
        return jsonify({'success': True, 'next_review': progress.next_review_date.isoformat()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
