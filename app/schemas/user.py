from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class User(Document):
    email: Indexed(EmailStr, unique=True) # type: ignore
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "users"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str # OAuth2 password flow uses 'username' field, typically mapped to email
    password: str
