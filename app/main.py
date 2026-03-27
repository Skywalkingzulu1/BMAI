import os
from datetime import datetime, timedelta
from typing import Literal, Optional, Dict

import stripe
from fastapi import Depends, FastAPI, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, validator

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

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
if not STRIPE_SECRET_KEY:
    raise RuntimeError("STRIPE_SECRET_KEY environment variable not set")
stripe.api_key = STRIPE_SECRET_KEY


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
    role: Literal["driver", "logistics"]
    is_active: bool = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Literal["driver", "logistics"]

    @validator("role")
    def role_must_be_valid(cls, v):
        if v not in ("driver", "logistics"):
            raise ValueError("role must be either 'driver' or 'logistics'")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[Literal["driver", "logistics"]] = None


# ----------------------------------------------------------------------
# FastAPI app
# ----------------------------------------------------------------------
app = FastAPI(title="Drive Online API")


# ----------------------------------------------------------------------
# Dependency helpers
# ----------------------------------------------------------------------
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_token(token)
    email: str = payload.get("sub")
    role: str = payload.get("role")
    if email is None or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user = users_db.get(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token role does not match user role",
        )
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_driver(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != "driver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation permitted for drivers only",
        )
    return current_user


def get_current_logistics(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != "logistics":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation permitted for logistics companies only",
        )
    return current_user


# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate):
    """Register a new driver or logistics company."""
    if user_in.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed,
        role=user_in.role,
        is_active=True,
    )
    users_db[user.email] = user
    return user


@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user and return a JWT token.
    The form fields are:
    - username: the user's email
    - password: the user's password
    - scope: (optional) can be used to request a specific role, but we ignore it here.
    """
    user = users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    return Token(access_token=access_token)


@app.get("/me", response_model=User)
def read_current_user(current_user: User = Depends(get_current_active_user)):
    """Return the authenticated user's details."""
    return current_user


@app.get("/driver/dashboard")
def driver_dashboard(driver: User = Depends(get_current_driver)):
    """Example protected endpoint for drivers."""
    return {"msg": f"Welcome driver {driver.email}!"}


@app.get("/logistics/dashboard")
def logistics_dashboard(logistics: User = Depends(get_current_logistics)):
    """Example protected endpoint for logistics companies."""
    return {"msg": f"Welcome logistics company {logistics.email}!"}