
from fastapi import APIRouter, HTTPException, status

from backend.auth.schemas import RegisterRequest, LoginRequest
from backend.auth.security import (
    hash_password,
    verify_password,
    create_access_token
)
from backend.auth.database import get_user_by_email, create_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest):

    existing_user = get_user_by_email(data.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    hashed_password = hash_password(data.password)

    user = create_user(
        username=data.username,
        email=data.email,
        password_hash=hashed_password,
        role="viewer"
    )

    return {
        "message": "Registration successful",
        "role": user["role"]
    }


@router.post("/login")
def login(data: LoginRequest):

    user = get_user_by_email(data.email)

    if not user or not verify_password(
        data.password,
        user["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Corrected: pass user ID and role as separate arguments
    token = create_access_token(
        str(user["id"]),
        user["role"]
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "is_active": bool(user["is_active"])
        }
    }
