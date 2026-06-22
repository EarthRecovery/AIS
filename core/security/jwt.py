# app/security/jwt.py
import os, datetime
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("JWT_SECRET", "change-me")
ALGO = "HS256"
bearer_scheme = HTTPBearer(auto_error=False)

def create_access_token(sub: str, expires_minutes: int = 360) -> str:
    now = datetime.datetime.utcnow()
    payload = {"sub": sub, "exp": now + datetime.timedelta(minutes=expires_minutes), "iat": now}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGO)

def decode_access_token(token: str) -> str:
    """Decode JWT and return subject (e.g., user_id). Raises HTTPException on failure."""
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return data["sub"]

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = creds.credentials
    return decode_access_token(token)  # 返回 user_id 或其他标识
