import asyncio
from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app import models  # noqa: F401
from app.config import get_settings
from app.db.base import Base

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata

# PostGIS-owned tables that are not part of the Gonarra schema.
EXTENSION_TABLES = frozenset({"spatial_ref_sys"})


def include_object(
    obj: object, name: str | None, type_: str, reflected: bool, compare_to: object | None
) -> bool:
    """Only report real drift in `alembic check` / autogenerate.

    The schema is written as raw SQL migrations (DEC-029): indexes, partial unique indexes and
    comments live in SQL, not in the ORM models, so database-only indexes, unique indexes and
    extension tables are not drift. Columns, tables, types, nullability and named constraints
    declared in the models are still compared."""
    if type_ == "table" and name in EXTENSION_TABLES:
        return False
    return not (type_ in ("index", "unique_constraint") and reflected and compare_to is None)


def _comment_only(op_: Any) -> bool:
    return (
        op_.modify_nullable is None
        and op_.modify_server_default is False
        and op_.modify_name is None
        and op_.modify_type is None
    )


def process_revision_directives(context: object, revision: object, directives: list[Any]) -> None:
    """Drop comment-only operations (comments are documentation kept in the SQL migrations)."""
    from alembic.operations import ops

    for script in directives:
        for upgrade_ops in script.upgrade_ops_list:
            kept: list[Any] = []
            for op_ in upgrade_ops.ops:
                if isinstance(op_, ops.ModifyTableOps):
                    op_.ops = [
                        o
                        for o in op_.ops
                        if not isinstance(o, ops.CreateTableCommentOp | ops.DropTableCommentOp)
                        and not (isinstance(o, ops.AlterColumnOp) and _comment_only(o))
                    ]
                    if not op_.ops:
                        continue
                kept.append(op_)
            upgrade_ops.ops = kept


def do_run_migrations(connection: object) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=include_object,
        process_revision_directives=process_revision_directives,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        hide_parameters=True,  # log privacy: SQL parameters never appear in errors or logs
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    asyncio.run(run_async_migrations())
