"""
Password hashing and JWT issuance/verification for the Next.js frontend's
login/signup pages. Deliberately minimal - this is an MSc project demo, not
a production auth system - see the SECRET_KEY warning below before deploying
anywhere public.
"""
from __future__ import annotations

import os
import warnings
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

_DEV_DEFAULT_SECRET = "dev-insecure-secret-change-me-before-deploying-anywhere"
# `or` (not `.get(key, default)`) so a *present but empty* JWT_SECRET_KEY -
# e.g. "JWT_SECRET_KEY=" left blank in a .env file, which is a reasonable
# thing to do and not the same as the variable being absent - still falls
# back to the dev default instead of trying to sign with an empty string
# (which jwt.encode() rejects outright: "HMAC key must not be empty").
SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or _DEV_DEFAULT_SECRET
if SECRET_KEY == _DEV_DEFAULT_SECRET:
    warnings.warn(
        "JWT_SECRET_KEY is not set - using an insecure development default. "
        "Set a real random JWT_SECRET_KEY environment variable before deploying this anywhere reachable by others."
    )


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError (caught by the caller) if the token is invalid or expired."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
