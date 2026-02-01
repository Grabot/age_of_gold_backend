from sqlalchemy import types
from sqlmodel import Integer

class ZwaarArray(types.TypeDecorator):
    """Use ARRAY on PostgreSQL, JSON on other dialects (e.g. SQLite)."""
    impl = types.Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import ARRAY
            return dialect.type_descriptor(ARRAY(Integer()))
        else:
            return dialect.type_descriptor(types.JSON())

    def process_bind_param(self, value, dialect):
        if dialect.name != "postgresql" and value is not None:
            import json
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if dialect.name != "postgresql" and value is not None:
            import json
            return json.loads(value) if isinstance(value, str) else value
        return value
