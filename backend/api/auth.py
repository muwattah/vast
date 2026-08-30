from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from backend.database.db import get_db
from backend.models.property import User
from backend.auth.security import hash_password, verify_password, create_access_token
from backend.auth.deps import get_current_user

router = APIRouter()

class RegisterIn(BaseModel):
    email: str
    password: str
    @field_validator("password")
    @classmethod
    def strong_enough(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class LoginIn(BaseModel):
    email: str
    password: str

@router.post("/auth/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(400, "Email already registered")
    user = User(email=body.email.lower(), hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user.email), "token_type": "bearer", "email": user.email}

@router.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_access_token(user.email), "token_type": "bearer", "email": user.email}

@router.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email}
