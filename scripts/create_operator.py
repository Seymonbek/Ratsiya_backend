"""
Operator yaratish skripti (CLI).

Terminal orqali tez operator yaratish uchun (Swagger'siz).

Ishlatilishi:
    python -m scripts.create_operator
    python -m scripts.create_operator --username admin --password admin123 --name "Admin"
"""

import argparse
import asyncio
import sys

from app.core.security import hash_password
from app.db.session import async_session_factory
from app.enums import UserRole
from app.repositories.user import user_repository


async def create_operator(username: str, password: str, full_name: str) -> None:
    """Operator yaratish."""
    async with async_session_factory() as session:
        # Username band emasligini tekshirish
        if await user_repository.exists_by_username(session, username):
            print(f"❌ Xato: '{username}' allaqachon band")
            sys.exit(1)

        # Operator yaratish
        user = await user_repository.create(
            db=session,
            username=username,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=UserRole.OPERATOR,
        )
        await session.commit()

        print(f"✓ Operator yaratildi:")
        print(f"  ID:       {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Ism:      {user.full_name}")
        print(f"  Rol:      {user.role}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Operator yaratish")
    parser.add_argument("--username", default="admin", help="Login nomi")
    parser.add_argument("--password", default="admin123", help="Parol")
    parser.add_argument("--name", default="Administrator", help="To'liq ism")
    args = parser.parse_args()

    asyncio.run(create_operator(args.username, args.password, args.name))


if __name__ == "__main__":
    main()
