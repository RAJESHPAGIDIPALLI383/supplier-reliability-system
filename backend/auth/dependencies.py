
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

from backend.auth.database import get_auth_connection
from backend.auth.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    connection = get_auth_connection()

    try:
        user = connection.execute(
            """
            SELECT id, username, email, role, is_active
            FROM app_users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()
    finally:
        connection.close()

    if not user or not user["is_active"]:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive"
        )

    return dict(user)


def require_roles(*allowed_roles):
    def role_checker(user=Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this resource"
            )
        return user

    return role_checker
