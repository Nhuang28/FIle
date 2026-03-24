# LearnLoop

LearnLoop is a web-based flashcard application designed to help students master subjects through active recall and spaced repetition. It features a role-based system for Teachers and Students, allowing for class management, deck creation, and progress tracking.

## Features

-   **Role-Based Access Control**:
    -   **Teachers**: Create classes, manage decks, and assign study materials to students.
    -   **Students**: Join classes, study assigned decks, and track their learning progress.
-   **Deck Management**: Supports multiple question types including:
    -   **Flashcards**: Standard front/back cards.
    -   **Multiple Choice Questions (MCQ)**: Select the correct answer from options.
    -   **Fill-in-the-Gap**: Complete sentences by filling in missing words.
-   **Study Mode**:
    -   **Spaced Repetition System (SRS)**: Uses a modified SM-2 algorithm to schedule card reviews based on performance.
    -   **Interactive Sessions**: Real-time feedback and progress saving.
-   **Statistics**: Visual analytics for tracking study performance and accuracy over time.
-   **Class System**: Invite codes for easy student enrollment.

## Technology Stack

-   **Backend**: Python, Flask, SQLAlchemy
-   **Database**: SQLite
-   **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
-   **Authentication**: Flask-Login

## Installation & Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd learn-loop
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration**:
    -   Create a `.env` file in the root directory.
    -   Add necessary environment variables (e.g., `SECRET_KEY`, `DATABASE_URL`).

5.  **Initialize the Database**:
    ```bash
    flask db upgrade
    # OR if using a seed script
    python seed_data.py
    ```

6.  **Run the Application**:
    ```bash
    flask run
    ```
    Access the app at `http://127.0.0.1:5000`.

## Gemini API Setup & AI Quiz Generation

LearnLoop uses Google's Gemini API to automatically generate multiple-choice questions from source text.

### Setup Instructions

1.  **Get an API Key**:
    -   Visit [Google AI Studio](https://aistudio.google.com/).
    -   Create a new project (or select an existing one) and generate an API key.

2.  **Configure Environment**:
    -   Add the key to your `.env` file:
        ```bash
        GEMINI_API_KEY=your_api_key_here
        ```

### AI Quiz Generation Logic

The AI generation process converts raw educational text into structured database records.

**Location**: `app/routes/decks.py` -> `ai_generate` function.

**Workflow**:
1.  **Input**: User provides source text, number of questions, and difficulty level.
2.  **Prompt Engineering**:
    -   The system constructs a strict prompt instructing Gemini to act as an educational AI.
    -   It explicitly requests the output effectively as a **JSON list of objects**, enforcing a specific schema:
        ```json
        [
            {
                "question": "...",
                "options": ["A", "B", "C", "D"],
                "answer": "Correct Option",
                "explanation": "..."
            }
        ]
        ```
    -   This prevents the model from returning conversational text or markdown formatting that would break the parser.
3.  **Parsing & Validation**:
    -   The application receives the raw response and cleans it (removing potential markdown backticks).
    -   It matches the JSON structure to ensure all required fields (`question`, `options`, `answer`) are present.
    -   It calculates the `correct_index` by finding the position of the correct answer within the options list.
4.  **Database Storage**:
    -   Valid questions are saved to the `cards` table (as `CardMCQ` type) and linked to the active deck.

## Key Logic & Algorithms

### Spaced Repetition Algorithm (SM-2)

The core study logic implements a variation of the SuperMemo-2 (SM-2) algorithm to optimize long-term retention. It adjusts the review interval of a card based on the user's self-assessed quality of recall (0-5 scale).

**Location**: `app/routes/study.py` -> `save_progress` function.

**Variables**:
-   `EF` (Ease Factor): A multiplier indicating how easy a card is to remember. Default is 2.50.
-   `I` (Interval): Days until next review.
-   `n` (Repetitions): Number of consecutive successful recalls.
-   `q` (Quality): User rating (0=Blackout, 5=Perfect).

**Logic Flow**:
1.  **If Quality < 3 (Incorrect/Forgot)**:
    -   Repetitions (`n`) reset to 0.
    -   Interval (`I`) set to 1 day.
2.  **If Quality >= 3 (Correct)**:
    -   If `n` = 0, `I` = 1.
    -   If `n` = 1, `I` = 6.
    -   If `n` > 1, `I` = `Previous Interval` * `Current EF`.
    -   Increment `n`.
3.  **Update Ease Factor (EF)**:
    -   Formula: `EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))`
    -   Minimum `EF` is capped at 1.3 to prevent intervals from shrinking too drastically.

### Study Session Management

**Location**: `app/routes/study.py` -> `session` route.

-   **Access Control**: Checks if the user is the owner OR if the deck is shared with a class the user is enrolled in.
-   **Data Preparation**: Fetches all cards for the deck and formats them into a JSON-serializable list of dictionaries. This includes handling polymorphic relationships (Flashcard, MCQ, FillGap) to extract type-specific data (e.g., options for MCQs, answers for FillGaps).
-   **Frontend Integration**: The prepared data is injected into the template, allowing JavaScript to handle the interactive study session without page reloads for each card.
