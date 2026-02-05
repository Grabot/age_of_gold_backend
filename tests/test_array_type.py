"""Test for ZwaarArray type decorator."""

from sqlalchemy.dialects.postgresql import dialect as postgresql_dialect
from sqlalchemy.dialects.sqlite import dialect as sqlite_dialect

from src.models.model_util.zwaar_array import ZwaarArray


def test_zwaar_array_postgresql() -> None:
    """Test ZwaarArray with PostgreSQL dialect."""
    array_type = ZwaarArray()
    pg_impl = array_type.load_dialect_impl(postgresql_dialect())

    assert "ARRAY" in str(pg_impl)

    test_data = [1, 2, 3]
    result = array_type.process_bind_param(test_data, postgresql_dialect())
    assert result == test_data

    result = array_type.process_result_value(test_data, postgresql_dialect())
    assert result == test_data


def test_zwaar_array_sqlite() -> None:
    """Test ZwaarArray with SQLite dialect."""
    array_type = ZwaarArray()
    sqlite_impl = array_type.load_dialect_impl(sqlite_dialect())

    assert "Json" in str(sqlite_impl)

    test_data = [1, 2, 3]
    result = array_type.process_bind_param(test_data, sqlite_dialect())
    assert result == "[1, 2, 3]"

    result = array_type.process_result_value("[1, 2, 3]", sqlite_dialect())
    assert result == [1, 2, 3]


def test_zwaar_array_none_values() -> None:
    """Test ZwaarArray with None values."""
    array_type = ZwaarArray()

    result = array_type.process_bind_param(None, sqlite_dialect())
    assert result is None

    result = array_type.process_result_value(None, sqlite_dialect())
    assert result is None


def test_zwaar_array_cache_ok() -> None:
    """Test that ZwaarArray has cache_ok set to True."""
    array_type = ZwaarArray()
    assert array_type.cache_ok is True
