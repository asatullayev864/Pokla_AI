from fastapi import APIRouter, HTTPException, status

from database.db import get_user_by_username
from auth.security import verify_password, create_access_token
from api.schemas import LoginRequest, Token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token)
def login(data: LoginRequest):
    user = get_user_by_username(data.username)

    if not user or not user["is_active"] or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login yoki parol noto'g'ri",
        )

    token = create_access_token({"sub": user["username"], "role": user["role"]})

    return Token(access_token=token, role=user["role"], username=user["username"])

