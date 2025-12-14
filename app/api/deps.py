from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client
from app.core.config import settings
from pydantic import BaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") # URL is just for docs

# Initialize Supabase Client (Service Role or Anon, preferably Anon for verify, but Service Role is safer for backend ops)
# Actually for verify_jwt, just the anon key is enough if we trust supabase signature verification?
# Standard pattern: verify token.
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

class AuthUser(BaseModel):
    id: str
    email: str

async def get_current_user(token: str = Depends(oauth2_scheme)) -> AuthUser:
    try:
        # Supabase-py 'get_user' verifies the JWT
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
             raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user_data = user_response.user
        
        return AuthUser(id=user_data.id, email=user_data.email or "")
        
    except Exception as e:
        print(f"Auth Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

