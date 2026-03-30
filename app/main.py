import os
from datetime import datetime, timedelta
from typing import Dict, Optional

import stripe
from fastapi import Depends, FastAPI, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ----------------------------------------------------------------------
# Settings & security utilities
# ----------------------------------------------------------------------


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Uses python-dotenv to read a .env file if present.
    """

    secret_key: str = "supersecretkey"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    email_token_expire_minutes: int = 60
    # Provide a default empty string so the app can start in test environments.
    stripe_secret_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Instantiate settings; validation occurs here.
settings = Settings()

# Security utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# The tokenUrl must match the path of the login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Stripe configuration
stripe.api_key = settings.stripe_secret_key

# ----------------------------------------------------------------------
# FastAPI app and models
# ----------------------------------------------------------------------


app = FastAPI(title="BMAI API", version="0.1.0")


class User(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    disabled: Optional[bool] = False


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# In‑memory "database"
fake_users_db: Dict[str, UserInDB] = {
    "alice": UserInDB(
        username="alice",
        email="alice@example.com",
        full_name="Alice Wonderland",
        hashed_password=pwd_context.hash("secret1"),
        disabled=False,
    ),
    "bob": UserInDB(
        username="bob",
        email="bob@example.com",
        full_name="Bob Builder",
        hashed_password=pwd_context.hash("secret2"),
        disabled=False,
    ),
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)


def get_user(username: str) -> Optional[UserInDB]:
    return fake_users_db.get(username)


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Validate username and password.

    Returns the user object if authentication succeeds, otherwise ``None``.
    """
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token.

    ``data`` should contain at least a ``sub`` key with the username.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token)


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's information."""
    return current_user
