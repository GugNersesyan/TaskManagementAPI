from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Optional
import time

from app.api.deps import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, RefreshTokenRequest
from app.services.user_service import authenticate_user, create_user, get_user_by_id
from app.core.security import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=['Auth'])

rate_limit_store: Dict[str, list] = {}


def check_rate_limit(request: Optional[Request], max_requests: int = 5, window_seconds: int = 60):
    if not request:
        return True
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{client_ip}"
    now = time.time()
    if key not in rate_limit_store:
        rate_limit_store[key] = []
    
    rate_limit_store[key] = [
        ts for ts in rate_limit_store[key] 
        if now - ts < window_seconds
    ]
    
    if len(rate_limit_store[key]) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )
    
    rate_limit_store[key].append(now)
    return True


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    check_rate_limit(None, max_requests=5, window_seconds=60)
    
    user = authenticate_user(db, data.email, data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid email or password',
        )
    
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role,
        )
    
    refresh_token = create_refresh_token(
        subject=str(user.id)
        )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/register", status_code=201)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    check_rate_limit(None, max_requests=3, window_seconds=60)
    
    user = create_user(db, user_in.username, user_in.email, user_in.password)

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")

    if not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return TokenResponse(
        access_token=create_access_token(
            subject=str(user.id),
            role=user.role,
        ),
        refresh_token=create_refresh_token(
            subject=str(user.id),
        ),
    )
