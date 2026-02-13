from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.db.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()