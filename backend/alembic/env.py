import asyncio
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import the Base and settings
from app.core.config import settings
from app.models.base import Base

# this is the Alembic Config object, which provides
# access to the config file and the sqlalchemy url.
config = context.config

# Interpret the config file for Python logging.
# FileConfig can only be used with logging.config fileConfig
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    # Use the URL from settings instead of the .ini file for consistency
    url = settings.DATABASE_URL

    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    async def do_run_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations_sync)

    asyncio.run(do_run_migrations())

def do_run_migrations_sync(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.DATABASE_URL

    context.configure(
        sqlalchemy_url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_proxy="postgresql",
    )

    with context.begin_transaction():
        context.run_migrations()

# Helper to avoid circular import or missing create_async_engine
from sqlalchemy.ext.asyncio import create_async_engine

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
