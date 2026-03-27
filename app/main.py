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
    role: Literal["driver", "company"]
    is_verified: bool = False


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Literal["driver", "company"]

    @validator("role")
    def role_must_be_valid(cls, v):
        if v not in ("driver", "company"):
            raise ValueError("role must be either 'driver' or 'company'")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PaymentIntentRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Amount in the smallest currency unit (e.g., cents)")


# ----------------------------------------------------------------------
# FastAPI app and routes
# ----------------------------------------------------------------------
app = FastAPI(title="Drive Online API")


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_token(token)
    email: str = payload.get("sub")
    if email is None or email not in users_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    return users_db[email]


@app.post("/register", response_model=Token)
async def register(user_in: UserCreate):
    if user_in.email in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed = get_password_hash(user_in.password)
    user = User(email=user_in.email, hashed_password=hashed, role=user_in.role, is_verified=False)
    users_db[user.email] = user
    access_token = create_access_token(data={"sub": user.email})
    return Token(access_token=access_token)


@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    return Token(access_token=access_token)


@app.post("/payment_intent")
async def create_payment_intent(
    payload: PaymentIntentRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Create a Stripe PaymentIntent for the authenticated user.
    Amount should be provided in the smallest currency unit (e.g., cents).
    """
    try:
        intent = stripe.PaymentIntent.create(
            amount=payload.amount,
            currency="zar",
            metadata={"user_email": current_user.email, "role": current_user.role},
        )
        return {"client_secret": intent.client_secret}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------
# Placeholder for additional routes (e.g., job listings, driver-company matching)
# ----------------------------------------------------------------------
# ... (other route implementations would go here)