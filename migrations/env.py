import asyncio
import os
from json import loads
from logging.config import fileConfig
from typing import Any, Callable, List, Optional, cast

from alembic import context
from celery.backends.database.session import ResultModelBase  # type: ignore
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.schema import SchemaItem
from sqlmodel import SQLModel
from typing_extensions import Literal

from app.config.config import settings

# Define the type for the filter_db_objects function
FilterDBObjectsType = Callable[
    [
        Any,
        Optional[str],
        Literal[
            "schema",
            "table",
            "column",
            "index",
            "unique_constraint",
            "foreign_key_constraint",
        ],
        bool,
        Optional[SchemaItem],
    ],
    bool,
]

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = [SQLModel.metadata, ResultModelBase.metadata]
for meta in target_metadata:
    meta.naming_convention = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

exclude_tables: List[str] = loads(cast(str, os.getenv("DB_EXCLUDE_TABLES", "[]")))


def filter_db_objects(
    object: Any,
    name: Optional[str],
    type_: Literal[
        "schema",
        "table",
        "column",
        "index",
        "unique_constraint",
        "foreign_key_constraint",
    ],
    reflected: bool,
    compare_to: Optional[SchemaItem],
) -> bool:
    if type_ == "table" and name is not None:
        return name not in exclude_tables
    if (
        type_ == "index"
        and name is not None
        and name.startswith("idx")
        and name.endswith("geom")
    ):
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=settings.ASYNC_DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=filter_db_objects,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Any) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=filter_db_objects,
        )
        context.run_migrations()


async def run_migrations_online() -> None:
    config_section = config.get_section(config.config_ini_section)

    if config_section is None:
        raise ValueError("Config section not found")

    config_section["sqlalchemy.url"] = settings.ASYNC_DB_URL
    connectable = AsyncEngine(
        engine_from_config(
            config_section,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
