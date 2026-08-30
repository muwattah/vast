from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.models.property import User
from backend.auth.security import decode_token

security = HTTPBearer(auto_error=False)

def get_current_user_optional(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not creds:
        return None
    email = decode_token(creds.credentials)
    if not email:
        return None
    return db.query(User).filter(User.email == email, User.is_active == True).first()

def get_current_user(user: Optional[User] = Depends(get_current_user_optional)) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user
