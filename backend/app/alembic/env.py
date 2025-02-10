import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 1) Загружаем .env
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Это backend/app/alembic
APP_DIR = os.path.dirname(BASE_DIR)  # Это backend/app
ROOT_DIR = os.path.dirname(APP_DIR)  # Это корень проекта

load_dotenv(os.path.join(ROOT_DIR, ".env"))  # Загружаем переменные из .env

# 2) Получаем параметры БД
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mysqlpassword")
DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "dentsdatabase")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 3) Передаём URL Alembic
config = context.config
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

# 4) Настраиваем логирование
fileConfig(config.config_file_name)

# 5) Подключаем модели
sys.path.append(APP_DIR)  # Добавляем backend/app в пути импорта
from models.models import Base  # Импортируем Base из моделей

target_metadata = Base.metadata

# 6) Функции миграции
def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
