import logging
import threading

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from supabase import Client, create_client

from app.core.config import settings

logger = logging.getLogger(__name__)


# Dummy endpoint for Swagger (since we use Supabase external auth)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Lazy loading Supabase Client with atomic initialization
_supabase: Client | None = None
_supabase_lock = threading.Lock()

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        with _supabase_lock:
            # Double-checked locking
            if _supabase is None:
                if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                    raise ValueError("Supabase configuration missing: SUPABASE_URL and SUPABASE_KEY must be set.")
                _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase

class AuthUser(BaseModel):
    id: str
    email: str

async def get_current_user(token: str = Depends(oauth2_scheme)) -> AuthUser:
    try:
        client = get_supabase()
        
        # Supabase-py 'get_user' verifies the JWT
        user_response = client.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user_data = user_response.user
        return AuthUser(id=user_data.id, email=user_data.email or "")
        
    except HTTPException:
        # Re-raise HTTPExceptions (like the 401 above) directly
        raise
    except Exception as e:
        # Log minimal details for unexpected errors
        logger.error(f"Unexpected authentication error: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

