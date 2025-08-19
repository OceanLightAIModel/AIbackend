# app/route/user.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Users
from utils import get_current_user
from schemas import UserResponse, UserPreferenceUpdate

user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.get("/me", response_model=UserResponse)
def read_user_me(user: Users = Depends(get_current_user)):
    return user

@user_router.patch("/me", response_model=UserResponse)
def update_user_me(
    prefs: UserPreferenceUpdate,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user),
):
    if prefs.chat_theme is not None:
        user.chat_theme = prefs.chat_theme
    if prefs.dark_mode is not None:
        user.dark_mode = prefs.dark_mode
    db.commit()
    db.refresh(user)
    return user

@user_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_me(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    db.delete(user)
    db.commit()
    return
