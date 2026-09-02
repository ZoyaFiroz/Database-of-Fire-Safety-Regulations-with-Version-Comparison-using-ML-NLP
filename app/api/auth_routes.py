"""Register/login/me endpoints for the Next.js frontend's auth pages."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    email: str


TokenResponse.model_rebuild()


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    # Emails are stored and looked up in lowercase throughout this module.
    # Without this, "Name@Example.com" at registration and "name@example.com"
    # at login are treated as two different accounts by SQLite's default
    # case-sensitive TEXT comparison - login then fails with the generic
    # "Incorrect email or password" message even though the password typed
    # was correct, since the row is never found in the first place. Almost
    # every real mail provider treats the local part case-insensitively, so
    # normalising here matches user expectation, not just convenience.
    normalized_email = body.email.lower()
    existing = db.query(User).filter_by(email=normalized_email).first()
    if existing is not None:
        raise HTTPException(409, "An account with this email already exists")

    user = User(email=normalized_email, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, user=UserResponse(id=user.id, email=user.email))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email.lower()).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")

    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, user=UserResponse(id=user.id, email=user.email))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, email=current_user.email)
