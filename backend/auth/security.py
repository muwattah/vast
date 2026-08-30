"""Password hashing (PBKDF2) and JWT tokens."""
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets
from jose import jwt, JWTError
from backend.config import get_settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2:{salt}:{dk.hex()}"

def verify_password(plain: str, hashed: str) -> bool:
    try:
        algo, salt, hexdigest = hashed.split(":", 2)
        if algo != "pbkdf2":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt.encode("utf-8"), 120_000)
        return secrets.compare_digest(dk.hex(), hexdigest)
    except Exception:
        return False

def create_access_token(subject: str, expires_hours: int = ACCESS_TOKEN_EXPIRE_HOURS) -> str:
    settings = get_settings()
    secret = getattr(settings, "secret_key", None) or "dev-change-me-in-production"
    expire = datetime.utcnow() + timedelta(hours=expires_hours)
    return jwt.encode({"sub": subject, "exp": expire}, secret, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[str]:
    settings = get_settings()
    secret = getattr(settings, "secret_key", None) or "dev-change-me-in-production"
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
