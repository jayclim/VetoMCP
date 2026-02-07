from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select

from database import get_session
from models import User


def get_current_user(
    x_user_username: str = Header(...),
    session: Session = Depends(get_session),
) -> User:
    """Find or create a user based on the X-User-Username header."""
    user = session.exec(select(User).where(User.username == x_user_username)).first()
    if not user:
        user = User(username=x_user_username)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user
