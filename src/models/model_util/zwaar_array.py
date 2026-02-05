import json
from typing import List, Optional, Union, cast

from sqlalchemy import types
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.sql.type_api import TypeEngine
from sqlmodel import Integer


class ZwaarArray(types.TypeDecorator[List[int]]):
    """Use ARRAY on PostgreSQL, JSON on other dialects (e.g. SQLite)."""

    impl = types.Text
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[List[int]]:
        if dialect.name == "postgresql":
            return cast(
                TypeEngine[List[int]],
                dialect.type_descriptor(ARRAY(Integer())),  # type: ignore[no-untyped-call]
            )
        else:
            return cast(
                TypeEngine[List[int]],
                dialect.type_descriptor(types.JSON()),  # type: ignore[no-untyped-call]
            )

    def process_bind_param(  # type: ignore[override]
        self, value: Optional[List[int]], dialect: Dialect
    ) -> Optional[Union[str, List[int]]]:
        if dialect.name != "postgresql" and value is not None:
            return json.dumps(value)
        return value

    def process_result_value(  # type: ignore[override]
        self, value: Optional[Union[str, List[int]]], dialect: Dialect
    ) -> Optional[Union[str, List[int]]]:
        if dialect.name != "postgresql" and value is not None:
            return json.loads(value) if isinstance(value, str) else value
        return value
