"""Test for ZwaarArray type decorator."""

from sqlmodel import Field, SQLModel

from src.models.model_util.array_type import ZwaarArray


class TestModel(SQLModel, table=True):
    """Test model for testing ZwaarArray."""

    id: int | None = Field(default=None, primary_key=True)
    data: list[int] = Field(default=[], sa_type=ZwaarArray)


def test_zwaar_array_postgresql():
    """Test ZwaarArray with PostgreSQL dialect."""
    from sqlalchemy.dialects.postgresql import dialect as postgresql_dialect  # pylint: disable=import-outside-toplevel

    array_type = ZwaarArray()
    pg_impl = array_type.load_dialect_impl(postgresql_dialect())

    # Should return ARRAY type for PostgreSQL
    assert "ARRAY" in str(pg_impl)

    # Test process_bind_param
    test_data = [1, 2, 3]
    result = array_type.process_bind_param(test_data, postgresql_dialect())
    assert result == test_data

    # Test process_result_value
    result = array_type.process_result_value(test_data, postgresql_dialect())
    assert result == test_data


def test_zwaar_array_sqlite():
    """Test ZwaarArray with SQLite dialect."""
    from sqlalchemy.dialects.sqlite import dialect as sqlite_dialect  # pylint: disable=import-outside-toplevel

    array_type = ZwaarArray()
    sqlite_impl = array_type.load_dialect_impl(sqlite_dialect())

    # Should return JSON type for SQLite (SQLite uses _SQLiteJson)
    assert "Json" in str(sqlite_impl)

    # Test process_bind_param - should convert to JSON string
    test_data = [1, 2, 3]
    result = array_type.process_bind_param(test_data, sqlite_dialect())
    assert result == "[1, 2, 3]"

    # Test process_result_value - should parse from JSON string
    result = array_type.process_result_value("[1, 2, 3]", sqlite_dialect())
    assert result == [1, 2, 3]


def test_zwaar_array_none_values():
    """Test ZwaarArray with None values."""
    from sqlalchemy.dialects.sqlite import dialect as sqlite_dialect  # pylint: disable=import-outside-toplevel

    array_type = ZwaarArray()

    # Test process_bind_param with None
    result = array_type.process_bind_param(None, sqlite_dialect())
    assert result is None

    # Test process_result_value with None
    result = array_type.process_result_value(None, sqlite_dialect())
    assert result is None


def test_zwaar_array_cache_ok():
    """Test that ZwaarArray has cache_ok set to True."""
    array_type = ZwaarArray()
    assert array_type.cache_ok is True


def test_zwaar_array_integration():
    """Integration test for ZwaarArray with SQLModel."""
    # Test that the type can be used in a model
    model = TestModel(data=[1, 2, 3])
    assert model.data == [1, 2, 3]

    # Test with empty list
    model_empty = TestModel(data=[])
    assert model_empty.data == []
