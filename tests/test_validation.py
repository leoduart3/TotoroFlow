import pytest

from app.main import validate_name, validate_need, validate_roles


def test_name_accepts_common_spanish_name():
    assert validate_name("  María del Mar  ") == "María del Mar"


@pytest.mark.parametrize("name", ["A1ex", "Ana!", "A", "x" * 61])
def test_name_rejects_numbers_symbols_and_bad_lengths(name):
    with pytest.raises(ValueError):
        validate_name(name)


def test_roles_must_be_selected_from_catalog():
    assert validate_roles(["Caja", "Cocina", "Caja"]) == ["Caja", "Cocina"]
    with pytest.raises(ValueError):
        validate_roles(["Inventado"])


def test_need_requires_valid_time_range():
    validate_need(0, "Caja", 8, 16, 1)
    with pytest.raises(ValueError):
        validate_need(0, "Caja", 16, 8, 1)
