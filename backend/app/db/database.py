
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ..core.config import settings
from ..models.models import Base

DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Инициализирует базу данных:
      1. Создаёт базу данных, если её нет.
      2. Создаёт все таблицы, если их нет.
    """
    # Формируем URL подключения без указания имени БД
    base_url = DATABASE_URL.rsplit('/', 1)[0]
    tmp_engine = create_engine(base_url, echo=False)

    # Создаём базу данных, если её не существует
    with tmp_engine.connect() as connection:
        connection.execute(
            text(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}")
        )

    # Создаём все таблицы, определённые в Base
    Base.metadata.create_all(bind=engine)