from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from supabase import create_client, Client
from app.core.config import settings
from pydantic import BaseModel

# Dummy endpoint for Swagger (since we use Supabase external auth)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Lazy loading Supabase Client to prevent cold-start crashes if env vars missing
_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase

class AuthUser(BaseModel):
    id: str
    email: str

import logging

logger = logging.getLogger(__name__)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> AuthUser:
    try:
        # Lazy load client
        client = get_supabase()
        
        # Supabase-py 'get_user' verifies the JWT
        user_response = client.auth.get_user(token)
        if not user_response or not user_response.user:
             raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user_data = user_response.user
        
        return AuthUser(id=user_data.id, email=user_data.email or "")
        
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

