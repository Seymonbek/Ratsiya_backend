from fastapi import HTTPException, status

from app.enums import UserRole
from app.models.user import User


def check_is_operator(user: User) -> None:

    if user.role != UserRole.OPERATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat operator bu amalni bajara oladi",
        )


def check_is_driver(user: User) -> None:

    if user.role != UserRole.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat driver bu amalni bajara oladi",
        )
