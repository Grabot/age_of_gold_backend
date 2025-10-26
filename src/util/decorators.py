"""File for decorators."""

import inspect
from functools import wraps
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Optional,
    TypeVar,
    Union,
    get_type_hints,
)

from fastapi import Response, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.util.gold_logging import logger
from src.util.util import get_failed_response

T = TypeVar("T")


def handle_db_errors(
    default_error_message: str = "Internal server error",
    default_status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> Callable[
    [Callable[..., Coroutine[Any, Any, T]]],
    Callable[..., Coroutine[Any, Any, Union[T, Dict[str, Union[bool, str]]]]],
]:
    """
    Decorator to handle database errors and rollback.
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, Union[T, Dict[str, Union[bool, str]]]]]:
        type_hints = get_type_hints(func)
        response_param_name = None
        db_param_name = None

        for name, type_ in type_hints.items():
            if type_ is Response:
                response_param_name = name
            elif type_ is AsyncSession:
                db_param_name = name

        @wraps(func)
        async def wrapper(
            *args: Any, **kwargs: Any
        ) -> Union[T, Dict[str, Union[bool, str]]]:
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            response: Optional[Response] = None
            db: Optional[AsyncSession] = None

            if response_param_name:
                response = bound_args.arguments.get(response_param_name)
                # TODO: probably remove?
                if not isinstance(response, Response):
                    response = None

            if db_param_name:
                db = bound_args.arguments.get(db_param_name)
                # TODO: probably remove?
                if not isinstance(db, AsyncSession):
                    db = None

            if response is None or db is None:
                logger.error("Failed to extract response or db from function arguments")
                if response is None:
                    response = Response()
                return get_failed_response(
                    "Invalid function call", response, status.HTTP_409_CONFLICT
                )

            try:
                return await func(*args, **kwargs)
            except IntegrityError as e:
                logger.error("Database integrity error: %s", e)
                await db.rollback()
                return get_failed_response(
                    "Database constraint violation", response, status.HTTP_409_CONFLICT
                )
            except SQLAlchemyError as e:
                logger.error("Database error: %s", e)
                await db.rollback()
                return get_failed_response(
                    default_error_message, response, default_status_code
                )
            except Exception as e:
                logger.error("Unexpected error: %s", e)
                await db.rollback()
                return get_failed_response(
                    default_error_message, response, default_status_code
                )

        return wrapper

    return decorator
