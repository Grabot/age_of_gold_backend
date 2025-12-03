"""File for decorators."""

import inspect
from functools import wraps
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar, cast, get_type_hints

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.util.gold_logging import logger

P = ParamSpec("P")
T = TypeVar("T")


def handle_db_errors(
    default_error_message: str = "Internal server error",
    default_status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]
]:
    """
    Decorator to handle database errors and rollback.
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[P, Coroutine[Any, Any, T]]:
        type_hints = get_type_hints(func)
        db_param_name = None

        for name, type_ in type_hints.items():
            if type_ is AsyncSession:
                db_param_name = name

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            if (
                db_param_name is None
                or db_param_name not in bound_args.arguments
                or bound_args.arguments[db_param_name] is None
            ):
                logger.error("Failed to extract response or db from function arguments")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Invalid function call",
                )

            db: AsyncSession = cast(
                AsyncSession, bound_args.arguments.get(db_param_name)
            )

            try:
                return await func(*args, **kwargs)
            except IntegrityError as e:
                logger.error("Database integrity error: %s", e)
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Database constraint violation",
                )
            except SQLAlchemyError as e:
                logger.error("Database error: %s", e)
                await db.rollback()
                raise HTTPException(
                    status_code=default_status_code,
                    detail=default_error_message,
                )
            except HTTPException:
                # Re-raise HTTPException to let FastAPI handle it
                # Make sure no database changes are made when raising an HTTPException
                raise
            except Exception as e:
                logger.error("Unexpected error: %s", e)
                await db.rollback()
                raise HTTPException(
                    status_code=default_status_code,
                    detail=default_error_message,
                )

        return wrapper

    return decorator
