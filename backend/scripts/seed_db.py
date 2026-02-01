import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from sqlalchemy.orm import configure_mappers
from app.models import user, repository, documentation, chat
from app.core.database import Base
from app.core.security import get_password_hash

def seed():
    # Create tables
    configure_mappers()
    Base.metadata.create_all(bind=engine)
    
    # Seed data
    db = SessionLocal()
    try:
        # 1. Create Test User
        test_email = "test@docubot.com"
        existing_user = db.query(user.User).filter(user.User.email == test_email).first()
        
        if not existing_user:
            test_user = user.User(
                email=test_email,
                hashed_password=get_password_hash("password123"),
                full_name="Test User",
                is_active=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"👤 Created user: {test_email}")

            # 2. Create Test Repository
            test_repo = repository.Repository(
                user_id=test_user.id,
                github_id=123456,
                name="docubot-mvp",
                full_name="test/docubot-mvp",
                description="A test repository for DocuBot",
                url="https://github.com/test/docubot-mvp",
                is_active=True
            )
            db.add(test_repo)
            db.commit()
            print(f"📁 Created repository: {test_repo.name}")
        else:
            print(f"👤 User {test_email} already exists")

        print("✅ Database seeded successfully")
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
