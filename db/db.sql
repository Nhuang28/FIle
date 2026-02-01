-- =========================================================
-- LearnLoop - Full MySQL/InnoDB Schema (MySQL 8.0+)
-- Charset: utf8mb4
-- =========================================================

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- ---------- USERS ----------
CREATE TABLE users (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL UNIQUE,
  email VARCHAR(255) NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('student', 'teacher') NOT NULL,
  last_active_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_users_role ON users(role);


-- ---------- CLASSES (Teacher creates class, gets invite_code) ----------
CREATE TABLE classes (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  teacher_id BIGINT UNSIGNED NOT NULL,
  name VARCHAR(150) NOT NULL,
  invite_code CHAR(6) NOT NULL UNIQUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_classes_teacher ON classes(teacher_id);


-- ---------- CLASS MEMBERS (Student joins by invite_code) ----------
CREATE TABLE class_members (
  class_id BIGINT UNSIGNED NOT NULL,
  student_id BIGINT UNSIGNED NOT NULL,
  joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (class_id, student_id),
  FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_class_members_student ON class_members(student_id);


-- ---------- DECKS (Student creates decks; optional share to a class) ----------
CREATE TABLE decks (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  owner_id BIGINT UNSIGNED NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT NULL,

  -- If you want to allow a deck to be "attached" to a class for teacher visibility:
  class_id BIGINT UNSIGNED NULL,

  visibility ENUM('private', 'class') NOT NULL DEFAULT 'private',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

  FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_decks_owner ON decks(owner_id);
CREATE INDEX idx_decks_class ON decks(class_id);
CREATE INDEX idx_decks_visibility ON decks(visibility);


-- ---------- CARDS (Deck contains many cards) ----------
CREATE TABLE cards (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  deck_id BIGINT UNSIGNED NOT NULL,

  card_type ENUM('flashcard', 'fill_gap', 'mcq') NOT NULL,

  -- Tracking source
  created_via ENUM('manual', 'ai') NOT NULL DEFAULT 'manual',
  ai_provider ENUM('openai', 'gemini') NULL,

  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

  FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_cards_deck ON cards(deck_id);
CREATE INDEX idx_cards_type ON cards(card_type);


-- ---------- CARD DETAILS (Subtype tables) ----------
-- Flashcard supports normal front/back and also Cloze template with {...}
CREATE TABLE card_flashcard (
  card_id BIGINT UNSIGNED PRIMARY KEY,

  -- For classic flashcard:
  front_text TEXT NULL,
  back_text  TEXT NULL,

  -- For Cloze deletion:
  -- Example: "I {prefer} tea to coffee."
  cloze_template TEXT NULL,

  -- Optional: store extracted answers (single or multiple) for cloze as JSON array, e.g. ["prefer"]
  answers_json JSON NULL,

  FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,

  CHECK (
    (front_text IS NOT NULL AND back_text IS NOT NULL)
    OR (cloze_template IS NOT NULL)
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE card_fill_gap (
  card_id BIGINT UNSIGNED PRIMARY KEY,
  question_text TEXT NOT NULL,

  -- Support multiple blanks/answers via JSON array, e.g. ["prefer"] or ["New York","NYC"]
  answers_json JSON NOT NULL,

  FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE card_mcq (
  card_id BIGINT UNSIGNED PRIMARY KEY,
  question_text TEXT NOT NULL,

  -- Flexible options count. Typical: ["A","B","C","D"]
  options_json JSON NOT NULL,

  -- 0-based index into options_json
  correct_index TINYINT UNSIGNED NOT NULL,

  explanation_text TEXT NULL,

  FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,

  CHECK (correct_index <= 20) -- safe upper bound; app validates options length
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ---------- SPACED REPETITION PROGRESS (per user per card) ----------
CREATE TABLE card_progress (
  user_id BIGINT UNSIGNED NOT NULL,
  card_id BIGINT UNSIGNED NOT NULL,

  last_review_at DATETIME NULL,
  next_review_date DATE NULL,

  -- Prefer DECIMAL over FLOAT for stability
  ease_factor DECIMAL(4,2) NOT NULL DEFAULT 2.50,
  reps INT UNSIGNED NOT NULL DEFAULT 0,
  lapses INT UNSIGNED NOT NULL DEFAULT 0,
  interval_days INT UNSIGNED NOT NULL DEFAULT 0,

  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (user_id, card_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,

  CHECK (ease_factor >= 1.30 AND ease_factor <= 5.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- For "Study Session only due cards": WHERE user_id=? AND next_review_date <= CURDATE()
CREATE INDEX idx_progress_due ON card_progress(user_id, next_review_date);
CREATE INDEX idx_progress_card ON card_progress(card_id);


-- ---------- REVIEW LOGS (for charts + teacher analytics + days since last study) ----------
CREATE TABLE review_logs (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  card_id BIGINT UNSIGNED NOT NULL,
  deck_id BIGINT UNSIGNED NOT NULL,

  reviewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  -- difficulty rating: 0..3 (exact requirement)
  difficulty_0_3 TINYINT UNSIGNED NOT NULL,

  -- Optional: correctness & captured answer (useful for charts and debugging)
  was_correct TINYINT(1) NULL,
  answer_text TEXT NULL,
  response_time_ms INT UNSIGNED NULL,

  -- Optional snapshots for debugging scheduling
  progress_before JSON NULL,
  progress_after  JSON NULL,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,
  FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE,

  CHECK (difficulty_0_3 IN (0,1,2,3))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_review_user_time ON review_logs(user_id, reviewed_at);
CREATE INDEX idx_review_deck_time ON review_logs(deck_id, reviewed_at);
CREATE INDEX idx_review_card_time ON review_logs(card_id, reviewed_at);


-- ---------- OPTIONAL: DAILY STATS (pre-aggregated for faster charts; can be derived from review_logs) ----------
CREATE TABLE study_daily_stats (
  user_id BIGINT UNSIGNED NOT NULL,
  study_date DATE NOT NULL,

  reviews_count INT UNSIGNED NOT NULL DEFAULT 0,
  correct_count INT UNSIGNED NOT NULL DEFAULT 0,
  total_attempts INT UNSIGNED NOT NULL DEFAULT 0,

  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (user_id, study_date),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ---------- OPTIONAL: GAMIFICATION SCORE (keep only if you really use it) ----------
CREATE TABLE student_scores (
  user_id BIGINT UNSIGNED PRIMARY KEY,
  current_score INT NOT NULL DEFAULT 0,
  last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
