"""
安全模块 — JWT 令牌生成与验证、密码哈希
"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码 — 使用 SHA-256 + salt"""
    parts = hashed_password.split("$")
    if len(parts) != 3:
        return False
    salt, stored_hash = parts[1], parts[2]
    computed = hashlib.sha256(f"{salt}{plain_password}".encode()).hexdigest()
    return computed == stored_hash


def hash_password(password: str) -> str:
    """哈希密码 — SHA-256 + 随机 salt"""
    import secrets
    salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"sha256${salt}${pw_hash}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """解码 JWT token，返回 payload 或 None"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
