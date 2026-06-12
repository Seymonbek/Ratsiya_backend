from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


_BCRYPT_MAX_BYTES = 72


def _truncate_password(password: str) -> bytes:
    """Parolni baytga aylantirib, 72 baytga qisqartirish (bcrypt cheklovi)."""
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:

    hashed = bcrypt.hashpw(_truncate_password(password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:

    try:
        return bcrypt.checkpw(
            _truncate_password(plain_password),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, role: str) -> str:

    # Token muddati
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Token ichidagi ma'lumot
    payload = {
        "sub": str(user_id),  # Kim — user ID
        "role": role,         # Qanday rol — operator/driver
        "exp": expire,        # Qachongacha amal qiladi
        "jti": uuid4().hex,   # Unikal token ID (revocation/blacklist uchun)
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return token


def decode_access_token(token: str) -> dict | None:

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        # Token yaroqsiz, muddati o'tgan, yoki buzilgan
        return None
