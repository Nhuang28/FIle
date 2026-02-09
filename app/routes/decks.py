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
        # Get question type, default to flashcard
        question_type = request.form.get('question_type', 'flashcard')
        
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
            question_type=question_type,
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

@bp.route('/<int:deck_id>')
@login_required
def view(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    
    # Permission Check
    # Allow if owner OR if it's a class deck and user is in that class
    has_access = False
    if deck.owner_id == current_user.id:
        has_access = True
    elif deck.visibility == 'class' and deck.class_id:
        # Check if user is enrolled in this class
        # Current user enrolled_classes is a list of ClassMember objects (based on main.py)
        # We need to check if deck.class_id is in the user's enrolled class IDs
        if any(m.class_id == deck.class_id for m in current_user.enrolled_classes):
            has_access = True
            
    if not has_access:
        flash('You do not have permission to view this deck.', 'error')
        return redirect(url_for('decks.list'))

    return render_template('decks/view.html', deck=deck)

@bp.route('/<int:deck_id>/add', methods=['GET', 'POST'])
@login_required
def add(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    
    # Permission Check (Same as view)
    if deck.owner_id != current_user.id:
        flash('You do not have permission to add cards to this deck.', 'error')
        return redirect(url_for('decks.view', deck_id=deck.id))
        
    if request.method == 'POST':
        # Create Card based on Deck Type
        from app.models import Card, CardFlashcard, CardFillGap, CardMCQ
        import json
        
        card = Card(deck_id=deck.id, card_type=deck.question_type)
        db.session.add(card)
        db.session.commit() # Commit to get card.id
        
        try:
            if deck.question_type == 'flashcard':
                front = request.form.get('front')
                back = request.form.get('back')
                
                if not front or not back:
                     raise ValueError("Front and Back text are required")
                     
                flashcard = CardFlashcard(
                    card_id=card.id,
                    front_text=front,
                    back_text=back
                )
                db.session.add(flashcard)
                
            elif deck.question_type == 'fill_gap':
                sentence = request.form.get('sentence')
                missing_word = request.form.get('missing_word')
                
                if not sentence or not missing_word:
                    raise ValueError("Sentence and missing word are required")
                
                # Simple logic: store as is. In future could auto-replace word in sentence with blank.
                fill_gap = CardFillGap(
                    card_id=card.id,
                    question_text=sentence,
                    answers_json=json.dumps([missing_word]) # Store as list of acceptable answers
                )
                db.session.add(fill_gap)
                
            elif deck.question_type == 'mcq':
                question = request.form.get('question')
                opt1 = request.form.get('option_1')
                opt2 = request.form.get('option_2')
                opt3 = request.form.get('option_3')
                opt4 = request.form.get('option_4')
                correct_idx = request.form.get('correct_index') # 0-3
                explanation = request.form.get('explanation')
                
                if not question or not all([opt1, opt2, opt3, opt4]) or correct_idx is None:
                    raise ValueError("All fields are required")
                
                mcq = CardMCQ(
                    card_id=card.id,
                    question_text=question,
                    options_json=json.dumps([opt1, opt2, opt3, opt4]),
                    correct_index=int(correct_idx),
                    explanation_text=explanation
                )
                db.session.add(mcq)
            
            db.session.commit()
            flash('Card added successfully!', 'success')
            return redirect(url_for('decks.add', deck_id=deck.id)) # Redirect back to add more
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding card: {str(e)}', 'error')
            # If error, maybe we should not redirect but render with valid errors? 
            # For MVP, redirecting back is safer to clear state found
    
    return render_template('decks/add_card.html', deck=deck)

@bp.route('/<int:deck_id>/edit', methods=['POST'])
@login_required
def edit(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    if deck.owner_id != current_user.id:
        flash('You do not have permission to edit this deck.', 'error')
        return redirect(url_for('decks.view', deck_id=deck.id))
    
    new_title = request.form.get('title')
    if new_title:
        deck.title = new_title
        db.session.commit()
        flash('Deck renamed successfully.', 'success')
        
    return redirect(url_for('decks.view', deck_id=deck.id))

@bp.route('/<int:deck_id>/delete', methods=['POST'])
@login_required
def delete(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    if deck.owner_id != current_user.id:
        flash('You do not have permission to delete this deck.', 'error')
        return redirect(url_for('decks.view', deck_id=deck.id))
        
    try:
        db.session.delete(deck)
        db.session.commit()
        flash('Deck deleted successfully.', 'success')
        return redirect(url_for('decks.list'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting deck: {str(e)}', 'error')
        return redirect(url_for('decks.view', deck_id=deck.id))

@bp.route('/<int:deck_id>/ai-generate', methods=['GET', 'POST'])
@login_required
def ai_generate(deck_id):
    from flask import current_app  # Import here to be available for entire function
    deck = Deck.query.get_or_404(deck_id)
    
    # Permission Check
    if deck.question_type != 'mcq':
        flash('AI Quiz Generation is only available for Multiple Choice Decks.', 'error')
        return redirect(url_for('decks.view', deck_id=deck.id))
        
    if request.method == 'POST':
        import json
        import os
        from dotenv import load_dotenv
        from app.models import Card, CardMCQ
        
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            flash('AI configuration missing (GEMINI_API_KEY not found in env).', 'error')
            return redirect(url_for('decks.view', deck_id=deck.id))
            
        source_content = request.form.get('source_content')
        num_questions = request.form.get('num_questions', 5)
        difficulty = request.form.get('difficulty', 'medium')
        
        if not source_content:
            flash('Source content is required.', 'error')
            return render_template('decks/ai_generator.html', deck=deck)
            
        try:
            from google import genai
            
            client = genai.Client(api_key=api_key)
            
            # Strict JSON Prompt
            prompt = f"""
            You are an educational AI. Generate {num_questions} multiple-choice questions (MCQ) based on the following content.
            Difficulty Level: {difficulty}.
            
            Content:
            {source_content}
            
            CRITICAL: Return the response STRICTLY as a raw JSON list of objects. 
            Do NOT use markdown code blocks (no ```json). 
            Do NOT include any preamble or postscript.
            
            Required Format:
            [
                {{
                    "question": "The question text here?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "answer": "The exact string of the correct option",
                    "explanation": "Comprehensive explanation of why the correct answer is right and why the other options are wrong."
                }}
            ]
            """
            
            # Model execution with retries
            import time
            response = None
            max_retries = 3
            model_name = 'gemini-flash-latest' # Update to gemini-flash-latest as requested
            
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=model_name, 
                        contents=prompt
                    )
                    break 
                except Exception as e:
                    if '429' in str(e) and attempt < max_retries - 1:
                        time.sleep(2 * (attempt + 1))
                    else:
                        raise e
            
            if not response or not response.text:
                raise Exception("AI returned empty response.")
            
            # Logging for Debugging
            print(f"AI Response Raw: {response.text}")
            
            # Clean and Parse
            text_response = response.text.strip()
            
            # JSON Extraction via Regex (Fallback if strict mode fails to be clean)
            import re
            json_match = re.search(r'\[.*\]', text_response, re.DOTALL)
            if json_match:
                text_response = json_match.group(0)
            else:
                # Fallback cleanups if regex fails or is not needed (e.g. strict raw)
                if text_response.startswith('```json'):
                    text_response = text_response[7:]
                if text_response.startswith('```'):
                    text_response = text_response[3:]
                if text_response.endswith('```'):
                    text_response = text_response[:-3]
            
            try:
                questions_data = json.loads(text_response.strip())
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {e}")
                print(f"Text tried to parse: {text_response}")
                raise e
            
            count = 0
            for q in questions_data:
                # Validation
                question_text = q.get('question')
                options = q.get('options')
                answer = q.get('answer')
                
                if not question_text or not options or not answer:
                    continue
                    
                # Calculate Correct Index
                try:
                    correct_index = options.index(answer)
                except ValueError:
                    print(f"Skipping: Answer '{answer}' not found in options {options}")
                    continue
                
                # Create Card
                card = Card(deck_id=deck.id, card_type='mcq')
                db.session.add(card)
                db.session.flush() # Get ID
                
                mcq = CardMCQ(
                    card_id=card.id,
                    question_text=question_text,
                    options_json=json.dumps(options),
                    correct_index=correct_index,
                    explanation_text=q.get('explanation', '')
                )
                db.session.add(mcq)
                count += 1
                
            db.session.commit()
            
            if count == 0:
                flash('AI generated response but 0 valid cards were created. Please check your source text.', 'warning')
            else:
                flash(f'Successfully generated {count} AI questions!', 'success')
                
            return redirect(url_for('decks.view', deck_id=deck.id))
            
        except json.JSONDecodeError:
            db.session.rollback()
            flash('AI returned invalid data format. Please try again or simplify content.', 'error')
            return render_template('decks/ai_generator.html', deck=deck, initial_content=source_content)
        except Exception as e:
            db.session.rollback()
            print(f"AI Generation Error: {str(e)}")
            flash(f'AI Error: {str(e)}', 'error')
            return render_template('decks/ai_generator.html', deck=deck, initial_content=source_content)

    return render_template('decks/ai_generator.html', deck=deck)
