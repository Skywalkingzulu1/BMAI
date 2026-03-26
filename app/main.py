import os
from datetime import datetime, timedelta
from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator

# ----------------------------------------------------------------------
# In‑memory "database"
# ----------------------------------------------------------------------
users_db: dict[str, "User"] = {}

# ----------------------------------------------------------------------
# Settings & security utilities
# ----------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
EMAIL_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_email_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=EMAIL_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": email, "exp": expire, "type": "email_verification"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
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


# ----------------------------------------------------------------------
# Dependency helpers
# ----------------------------------------------------------------------
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_token(token)
    email: str = payload.get("sub")
    if email is None or email not in users_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return users_db[email]


def require_role(required_role: str):
    def role_dependency(user: User = Depends(get_current_user)):
        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return role_dependency


# ----------------------------------------------------------------------
# FastAPI app & routes
# ----------------------------------------------------------------------
app = FastAPI(title="Drive Online Authentication API")


@app.post("/register", status_code=201)
def register(user_in: UserCreate):
    if user_in.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = get_password_hash(user_in.password)
    user = User(email=user_in.email, hashed_password=hashed, role=user_in.role)
    users_db[user.email] = user
    email_token = create_email_token(user.email)
    # NOTE: In a production system you would send this token via email.
    return {"msg": "User registered. Verify email using the provided token.", "email_token": email_token}


@app.get("/verify-email")
def verify_email(token: str):
    payload = decode_token(token)
    if payload.get("type") != "email_verification":
        raise HTTPException(status_code=400, detail="Invalid verification token")
    email = payload.get("sub")
    user = users_db.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    return {"msg": "Email verified successfully"}


@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    access_token = create_access_token({"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected/driver")
def driver_endpoint(user: User = Depends(require_role("driver"))):
    return {"msg": f"Hello Driver {user.email}"}


@app.get("/protected/company")
def company_endpoint(user: User = Depends(require_role("company"))):
    return {"msg": f"Hello Company {user.email}"}