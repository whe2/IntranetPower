import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict
from dotenv import load_dotenv

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
import models

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "secretkey1234567890supersecretkey")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# Simple Rate Limiting for Login (Brute Force Protection)
# Maps IP -> list of failed attempt timestamps
LOGIN_ATTEMPTS: Dict[str, list] = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME_SECONDS = 300 # 5 minutes lockout

def is_rate_limited(ip_address: str) -> bool:
    now = time.time()
    attempts = LOGIN_ATTEMPTS.get(ip_address, [])
    # Filter attempts within lockout window
    recent_attempts = [t for t in attempts if now - t < LOCKOUT_TIME_SECONDS]
    LOGIN_ATTEMPTS[ip_address] = recent_attempts
    return len(recent_attempts) >= MAX_LOGIN_ATTEMPTS

def record_failed_attempt(ip_address: str):
    now = time.time()
    if ip_address not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[ip_address] = []
    LOGIN_ATTEMPTS[ip_address].append(now)

def clear_failed_attempts(ip_address: str):
    if ip_address in LOGIN_ATTEMPTS:
        del LOGIN_ATTEMPTS[ip_address]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_token_from_request(request: Request, bearer_token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    # 1. Try Cookie
    token = request.cookies.get("access_token")
    if token:
        if token.startswith("Bearer "):
            return token[7:]
        return token
    # 2. Try Authorization Header
    if bearer_token:
        return bearer_token
    return None

def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se encontró token de autenticación",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido (sin sujeto)",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso inválido o expirado",
        )

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o no encontrado",
        )
    return user

def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role not in ["admin", "rrhh"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren permisos de Gestor/Administrador.",
        )
    return current_user
