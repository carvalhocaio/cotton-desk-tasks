from decimal import Decimal

import pytest

from desk.domain import (
    HVIParameters,
    LengthBelowMinimum,
    MicronaireOutOfRange,
    StrengthBelowMinimum,
    UniformityBelowMinimum,
)


def parameters(**overrides):
    """A commercially valid reading, with individual fields overridable."""
    values = {
        "micronaire": Decimal("4.2"),
        "length": Decimal("1.16"),
        "strength": Decimal("29.0"),
        "uniformity": Decimal("82.0"),
    }
    return HVIParameters(**{**values, **overrides})


def test_hvi_with_micronaire_within_range_is_valid():
    assert parameters().micronaire == Decimal("4.2")


def test_hvi_with_micronaire_below_range_raises_error():
    with pytest.raises(MicronaireOutOfRange):
        parameters(micronaire=Decimal("2.0"))


def test_hvi_with_micronaire_above_range_raises_error():
    with pytest.raises(MicronaireOutOfRange):
        parameters(micronaire=Decimal("7.5"))


def test_hvi_with_length_at_commercial_minimum_is_valid():
    assert parameters(length=Decimal("1.11")).length == Decimal("1.11")


def test_hvi_with_length_below_commercial_minimum_raises_error():
    with pytest.raises(LengthBelowMinimum):
        parameters(length=Decimal("1.05"))


def test_hvi_with_strength_at_commercial_minimum_is_valid():
    assert parameters(strength=Decimal("28.0")).strength == Decimal("28.0")


def test_hvi_with_strength_below_commercial_minimum_raises_error():
    with pytest.raises(StrengthBelowMinimum):
        parameters(strength=Decimal("24.0"))


def test_hvi_with_uniformity_at_commercial_minimum_is_valid():
    assert parameters(uniformity=Decimal("80.0")).uniformity == Decimal("80.0")


def test_hvi_with_uniformity_below_commercial_minimum_raises_error():
    with pytest.raises(UniformityBelowMinimum):
        parameters(uniformity=Decimal("76.0"))


def test_hvi_at_the_exact_upper_micronaire_bound_is_valid():
    """4.9 is marketable; the check is inclusive on both ends."""
    assert parameters(micronaire=Decimal("4.90")).micronaire == Decimal("4.9")


def test_hvi_just_past_the_upper_micronaire_bound_raises_error():
    with pytest.raises(MicronaireOutOfRange):
        parameters(micronaire=Decimal("4.91"))


@pytest.mark.parametrize(
    "reading", [Decimal("4.2"), "4.2", 4.2], ids=["decimal", "str", "float"]
)
def test_readings_are_normalized_to_exact_decimal(reading):
    """A CSV string and a float both land on the same exact Decimal.

    The float case matters: Decimal(4.2) would keep the binary expansion,
    so the domain routes floats through str() instead.
    """
    hvi = parameters(micronaire=reading)

    assert hvi.micronaire == Decimal("4.2")
    assert isinstance(hvi.micronaire, Decimal)


def test_readings_keep_the_precision_the_lab_reported():
    """Decimal("4.20") equals 4.2 but still renders the trailing zero."""
    hvi = parameters(micronaire=Decimal("4.20"))

    assert hvi.micronaire == Decimal("4.2")
    assert str(hvi.micronaire) == "4.20"
