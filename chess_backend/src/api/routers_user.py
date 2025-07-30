from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.models import UserCreate, UserOut, Token
from src.api.db import get_db, User
from src.api.security import get_password_hash, verify_password, create_access_token, oauth2_scheme, decode_access_token
from fastapi.security import OAuth2PasswordRequestForm
from typing import List

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# PUBLIC_INTERFACE
@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == user.username) | (User.email == user.email)).first():
        raise HTTPException(status_code=400, detail="Username or email already registered")
    hashed_pw = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# PUBLIC_INTERFACE
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# PUBLIC_INTERFACE
@router.get("/me", response_model=UserOut)
def get_profile(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# PUBLIC_INTERFACE
@router.get("/leaderboard", response_model=List[UserOut])
def get_leaderboard(db: Session = Depends(get_db), limit: int = 10):
    users = db.query(User).order_by(User.elo.desc()).limit(limit).all()
    return users

