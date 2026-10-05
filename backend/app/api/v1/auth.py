from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from app.core.db import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.base import User
from app.api.deps import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, response: Response, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")

    # Hash password and create user
    hashed_pw = get_password_hash(user_data.password)
    new_user = User(username=user_data.username, hashed_password=hashed_pw)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Issue JWT cookie
    token = create_access_token(data={"sub": str(new_user.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False, # Set to True in production
        path="/"
    )
    return {"message": "User registered successfully"}

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, response: Response, login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    # Find user
    result = await db.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Issue JWT cookie
    token = create_access_token(data={"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False, # Set to True in production
        path="/"
    )
    return {"message": "Login successful"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/", httponly=True, samesite="lax")
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "id": current_user.id}
