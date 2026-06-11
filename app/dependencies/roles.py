from fastapi import Depends

from app.core.permissions import check_is_operator, check_is_driver
from app.dependencies.auth import get_current_user
from app.models.user import User


async def require_operator(
    user: User = Depends(get_current_user),
) -> User:

    check_is_operator(user)
    return user


async def require_driver(
    user: User = Depends(get_current_user),
) -> User:

    check_is_driver(user)
    return user
