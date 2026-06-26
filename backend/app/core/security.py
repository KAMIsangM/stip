"""JWT and password security utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return _pwd_context.hash(password)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------


def _get_jwt_config() -> dict[str, Any]:
    cfg = get_settings().get("auth", {})
    return {
        "secret_key": cfg.get("jwt_secret_key", "sitp-dev-secret-change-in-production"),
        "algorithm": cfg.get("jwt_algorithm", "HS256"),
        "access_token_expire_minutes": cfg.get("jwt_access_token_expire_minutes", 480),
    }


def create_access_token(subject: int | str) -> str:
    """Create a JWT access token for the given user id."""
    jwt_cfg = _get_jwt_config()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=jwt_cfg["access_token_expire_minutes"]
    )
    to_encode = {"sub": str(subject), "exp": expire, "type": "access"}
    return jwt.encode(to_encode, jwt_cfg["secret_key"], algorithm=jwt_cfg["algorithm"])


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token. Returns payload or None."""
    jwt_cfg = _get_jwt_config()
    try:
        payload = jwt.decode(
            token, jwt_cfg["secret_key"], algorithms=[jwt_cfg["algorithm"]]
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> int | None:
    """Extract user_id from a valid JWT token."""
    payload = decode_access_token(token)
    if payload is None:
        return None
    sub = payload.get("sub")
    if sub is None:
        return None
    try:
        return int(sub)
    except (ValueError, TypeError):
        return None
