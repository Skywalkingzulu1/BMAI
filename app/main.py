import os
from datetime import datetime, timedelta
from typing import Literal, Optional, Dict

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator

# ----------------------------------------------------------------------
# In‑memory "database"
# ----------------------------------------------------------------------
# The key is the user's email address; the value is a User instance.
users_db: Dict[str, "User"] = {}

# ----------------------------------------------------------------------
# Settings & security utilities
# ----------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
EMAIL_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# The tokenUrl must match the path of the login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_password_hash(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    The token contains the supplied ``data`` and an expiration claim.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_email_token(email: str) -> str:
    """Create a token used for email verification (not used in this task)."""
    expire = datetime.utcnow() + timedelta(minutes=EMAIL_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": email, "exp": expire, "type": "email_verification"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode a JWT token and return its payload.

    Raises ``HTTPException`` with 401 if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc

# ----------------------------------------------------------------------
# Pydantic models
# ----------------------------------------------------------------------
class User(BaseModel):
    email: EmailStr
    hashed_password: str
    role: Literal["driver", "company"]
    is_verified: bool = False


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Literal["driver", "company"]

    @validator("password")
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[EmailStr] = None

# ----------------------------------------------------------------------
# Dependency helpers
# ----------------------------------------------------------------------
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Retrieve the current user based on the JWT token.

    The token is expected to contain a ``sub`` claim with the user's email.
    """
    payload = decode_token(token)
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject",
        )
    user = users_db.get(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

# ----------------------------------------------------------------------
# FastAPI application
# ----------------------------------------------------------------------
app = FastAPI(title="Driver Registration & Authentication API")


@app.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate):
    """Register a new driver or company.

    - Validates the payload via ``UserCreate``.
    - Checks for existing email.
    - Hashes the password and stores the user.
    - Returns a JWT access token for immediate authentication.
    """
    if user_in.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    hashed_pwd = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        role=user_in.role,
        is_verified=True,  # In a real app you would send a verification email.
    )
    users_db[user.email] = user
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return Token(access_token=access_token)


@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate a user and return a JWT token.

    ``OAuth2PasswordRequestForm`` expects ``username`` (used as email) and ``password`` fields.
    """
    user = users_db.get(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return Token(access_token=access_token)


@app.get("/me", response_model=User)
async def read_current_user(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's details (excluding the password hash)."""
    return current_user
