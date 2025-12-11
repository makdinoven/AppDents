# Исправление ошибки системы опросов

## Проблема

Возникала ошибка `LookupError: 'active' is not among the defined enum values` при обращении к `/api/surveys/pending`.

Причина: несоответствие регистра значений enum между кодом Python и базой данных:
- В БД: `DRAFT`, `ACTIVE`, `CLOSED` (верхний регистр)
- В коде Python было: `draft`, `active`, `closed` (нижний регистр)

## Что исправлено

### 1. Модели SQLAlchemy (`backend/app/models/models_v2.py`)
- `SurveyStatus`: значения изменены на верхний регистр (DRAFT, ACTIVE, CLOSED)
- `QuestionType`: значения изменены на верхний регистр (SINGLE_CHOICE, MULTIPLE_CHOICE, FREE_TEXT)

### 2. Схемы Pydantic (`backend/app/schemas_v2/survey.py`)
- Удален дублирующий enum `QuestionType`
- Теперь используется единый enum из `models_v2`

### 3. SQL миграции
- `001_create_surveys.sql`: обновлены значения enum на верхний регистр
- `002_fix_survey_enum_case.sql`: создан скрипт для миграции существующих данных

## Как применить исправление

### Для продакшн/тест сервера:

1. **Обновить код:**
   ```bash
   git pull
   ```

2. **Перезапустить бэкенд:**
   ```bash
   docker-compose restart backend
   # или
   docker-compose down && docker-compose up -d
   ```

3. **Применить SQL миграцию (если нужно):**
   
   Если в логах все еще появляется ошибка, выполните SQL скрипт:
   ```bash
   docker-compose exec backend python -c "
   from app.db.database import engine
   with open('/app/sql/002_fix_survey_enum_case.sql', 'r') as f:
       sql = f.read()
       with engine.connect() as conn:
           for statement in sql.split(';'):
               if statement.strip():
                   conn.execute(statement)
           conn.commit()
   "
   ```
   
   Или подключитесь к MySQL и выполните вручную:
   ```bash
   docker-compose exec mysql mysql -u root -p appdents < backend/app/sql/002_fix_survey_enum_case.sql
   ```

## Проверка

После применения исправления проверьте:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://test.dent-s.com/api/surveys/pending
```

Ответ должен быть успешным (200 OK) без ошибок.

## Примечания

- Все существующие данные в базе остаются неизменными (только регистр значений enum)
- Фронтенд получит enum значения в верхнем регистре (SINGLE_CHOICE вместо single_choice)
- Если фронтенд уже использует эти значения, нужно обновить проверки на фронтенде
