import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_password_hash, verify_password

def main():
    print("🔒 Testing Password Security...")
    
    test_cases = [
        "password123",
        "super_secret!",
        "another-test-pass"
    ]
    
    for pwd in test_cases:
        print(f"\nTesting: {pwd}")
        hashed = get_password_hash(pwd)
        print(f"   Hashed: {hashed}")
        
        # Verify correct
        is_valid = verify_password(pwd, hashed)
        print(f"   Verify (Correct): {'✅' if is_valid else '❌'}")
        
        # Verify incorrect
        is_invalid = verify_password(pwd + "_wrong", hashed)
        print(f"   Verify (Wrong):   {'✅' if not is_invalid else '❌'}")

if __name__ == "__main__":
    main()