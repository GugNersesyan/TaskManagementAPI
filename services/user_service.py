from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import verify_password, hash_password

def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user

def create_user(
        db: Session,
        username: str,
        email: str,
        password: str,
) -> User:
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    if existing_user:
        raise ValueError("Username or email already registered")
    
    hashed_password = hash_password(password)

    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return user

def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)