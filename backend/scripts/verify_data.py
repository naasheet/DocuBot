import sys
import os
import socket

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env before any app imports (so we have DATABASE_URL for local host swap)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# Fix for local execution: If 'postgres' hostname isn't resolvable, use 'localhost'
try:
    socket.gethostbyname("postgres")
except socket.gaierror:
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url and "@postgres" in db_url:
        print("[*] Local environment detected. Switching DB host to 'localhost'.")
        os.environ["DATABASE_URL"] = db_url.replace("@postgres", "@localhost")

from app.core.database import SessionLocal
from app.models import user, repository, chat, documentation

def verify():
    db = SessionLocal()
    try:
        print("[*] Verifying Database Data...")

        # Check Users
        users = db.query(user.User).all()
        print(f"\n[*] Users Found: {len(users)}")
        for u in users:
            print(f"   - ID: {u.id} | Email: {u.email} | Active: {u.is_active}")
            print(f"     Repositories: {len(u.repositories)}")

        # Check Repositories
        repos = db.query(repository.Repository).all()
        print(f"\n[*] Repositories Found: {len(repos)}")
        for r in repos:
            print(f"   - ID: {r.id} | Name: {r.full_name} | Owner ID: {r.user_id}")

    finally:
        db.close()

if __name__ == "__main__":
    verify()