from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_user: User, user_in: dict):
    for field, value in user_in.items():
        if field == "password" and value:
            hashed_password = get_password_hash(value)
            setattr(db_user, "hashed_password", hashed_password)
        else:
            setattr(db_user, field, value)
            
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user