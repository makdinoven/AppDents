# AppDents

Запуск приложения для разработки 

### docker compose -f docker-compose.dev.yaml up --build -d

Копирование миграций с контейнера на локальную машину

### docker cp backend_dev:/app/alembic/versions backend/app/alembic/

Создание миграции

### alembic revision --autogenerate -m "Добавлен новый столбец в таблицу XYZ"

Применение миграции 

### alembic upgrade head
