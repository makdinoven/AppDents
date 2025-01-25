
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Создание двигателя SQLAlchemy
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Создание сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Зависимость для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
