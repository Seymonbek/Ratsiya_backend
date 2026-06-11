import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.base import Base

from app.models import User, Driver  # noqa: F401

config = context.config

# alembic.ini dagi logging sozlamalarini qo'llash
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# DATABASE_URL ni .env dan olish alembic.ini da emas
# Bu muhim chunki URL bitta joyda config.py saqlanadi
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Target metadata — Alembic shu modellarni DB bilan solishtiradi
target_metadata = Base.metadata


def run_migrations_offline() -> None:

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Migratsiyani bajarish connection tayyor bo'lganda."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # compare_type=True → ustun turi o'zgarsa ham aniqlaydi
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Migratsiya uchun pool kerak emas
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Online rejimda migratsiya async."""
    asyncio.run(run_async_migrations())


# Qaysi rejimda ishlayotganini aniqlash
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
