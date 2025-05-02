import time

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from ..core.config import settings
from ..models.models_v2 import Base

DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    f"?charset=utf8"
)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True,)
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
    last_exc = None
    for attempt in range(10):
        print(f">>> attempt {attempt}")
        try:
            with tmp_engine.connect() as conn:
                print("Succes connection")
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}"))
            break
        except OperationalError as e:
            print(f">>> Failed connections {attempt}. Error: {e}")
            last_exc = e
            time.sleep(2)
    else:
        # не получилось ни разу — перекатим исключение дальше
        raise last_exc

    # Создаём все таблицы, определённые в Base
    Base.metadata.create_all(bind=engine)

    # Асинхронное подключение к БД
ASYNC_DATABASE_URL = (
     f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
     f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
