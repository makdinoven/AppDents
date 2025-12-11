-- ============================================
-- Миграция: Исправление регистра enum значений в таблицах опросов
-- ============================================
-- Эта миграция обновляет значения enum с нижнего регистра на верхний
-- для соответствия определению enum в базе данных

-- Обновляем статусы опросов
UPDATE surveys 
SET status = 'DRAFT' 
WHERE LOWER(status) = 'draft';

UPDATE surveys 
SET status = 'ACTIVE' 
WHERE LOWER(status) = 'active';

UPDATE surveys 
SET status = 'CLOSED' 
WHERE LOWER(status) = 'closed';

-- Обновляем типы вопросов
UPDATE survey_questions 
SET question_type = 'SINGLE_CHOICE' 
WHERE LOWER(question_type) = 'single_choice';

UPDATE survey_questions 
SET question_type = 'MULTIPLE_CHOICE' 
WHERE LOWER(question_type) = 'multiple_choice';

UPDATE survey_questions 
SET question_type = 'FREE_TEXT' 
WHERE LOWER(question_type) = 'free_text';

-- Проверяем результат
SELECT CONCAT('Surveys: ', COUNT(*), ' записей') as result FROM surveys;
SELECT CONCAT('Survey questions: ', COUNT(*), ' записей') as result FROM survey_questions;
