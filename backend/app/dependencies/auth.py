"""FastAPI dependency for JWT authentication.

Provides get_current_user() that extracts the authenticated user from
the Authorization header and returns the User ORM instance.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_user_id_from_token
from app.models import User

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT token and return the authenticated User.

    Raises 401 Unauthorized if the token is missing, invalid, or expired.
    """
    token = credentials.credentials
    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的认证令牌",
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )
    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Like get_current_user but returns None if no token is provided."""
    if credentials is None:
        return None
    user_id = get_user_id_from_token(credentials.credentials)
    if user_id is None:
        return None
    return db.get(User, user_id)
