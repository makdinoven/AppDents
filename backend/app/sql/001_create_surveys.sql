-- ============================================
-- Миграция: Создание таблиц системы опросов
-- ============================================

-- Таблица опросов
CREATE TABLE IF NOT EXISTS surveys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,
    title_key VARCHAR(100) NOT NULL,
    description_key VARCHAR(100),
    status ENUM('draft', 'active', 'closed') NOT NULL DEFAULT 'draft',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closed_at DATETIME,
    INDEX idx_surveys_slug (slug),
    INDEX idx_surveys_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Таблица вопросов
CREATE TABLE IF NOT EXISTS survey_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    survey_id INT NOT NULL,
    order_index INT NOT NULL,
    question_type ENUM('single_choice', 'multiple_choice', 'free_text') NOT NULL,
    text_key VARCHAR(100) NOT NULL,
    options_keys JSON,
    is_required BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (survey_id) REFERENCES surveys(id) ON DELETE CASCADE,
    INDEX idx_sq_survey (survey_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Таблица ответов
CREATE TABLE IF NOT EXISTS survey_responses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    survey_id INT NOT NULL,
    user_id INT NOT NULL,
    question_id INT NOT NULL,
    answer_choice JSON,
    answer_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (survey_id) REFERENCES surveys(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES survey_questions(id) ON DELETE CASCADE,
    INDEX idx_sr_user_survey (user_id, survey_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ============================================
-- Данные первого опроса: Складчина (Crowdfunding)
-- ============================================

INSERT INTO surveys (slug, title_key, description_key, status) 
VALUES ('crowdfunding-feature', 'survey.crowdfunding.title', 'survey.crowdfunding.description', 'active');

SET @survey_id = LAST_INSERT_ID();

-- Вопросы опроса
INSERT INTO survey_questions (survey_id, order_index, question_type, text_key, options_keys, is_required) VALUES
(@survey_id, 1, 'single_choice', 'survey.crowdfunding.q1.text', 
 '["survey.crowdfunding.q1.opt1", "survey.crowdfunding.q1.opt2", "survey.crowdfunding.q1.opt3", "survey.crowdfunding.q1.opt4"]', TRUE),
 
(@survey_id, 2, 'single_choice', 'survey.crowdfunding.q2.text', 
 '["survey.crowdfunding.q2.opt1", "survey.crowdfunding.q2.opt2", "survey.crowdfunding.q2.opt3"]', TRUE),
 
(@survey_id, 3, 'multiple_choice', 'survey.crowdfunding.q3.text', 
 '["survey.crowdfunding.q3.opt1", "survey.crowdfunding.q3.opt2", "survey.crowdfunding.q3.opt3", "survey.crowdfunding.q3.opt4"]', TRUE),
 
(@survey_id, 4, 'free_text', 'survey.crowdfunding.q4.text', NULL, FALSE);

