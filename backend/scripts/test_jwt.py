import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import create_access_token
from app.config import settings
from jose import jwt

def main():
    print("🔑 Testing JWT Token Generation...")
    
    user_email = "test@docubot.com"
    data = {"sub": user_email}
    
    print(f"   Creating token for: {user_email}")
    token = create_access_token(data)
    print(f"   Token: {token}")
    
    print("\n🔍 Verifying Token...")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"   Decoded Subject: {payload.get('sub')}")
        
        exp = payload.get("exp")
        if exp:
            exp_date = datetime.fromtimestamp(exp)
            print(f"   Expiration: {exp_date} (Local Time)")
            
            if exp > datetime.utcnow().timestamp():
                print("   Status: ✅ Valid (Not Expired)")
            else:
                print("   Status: ❌ Expired")
        else:
            print("   Status: ❌ No Expiration Claim")
            
    except Exception as e:
        print(f"   ❌ Error decoding token: {e}")

if __name__ == "__main__":
    main()