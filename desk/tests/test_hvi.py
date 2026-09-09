import pytest

from desk.domain import (
    HVIParameters,
    LengthBelowMinimum,
    MicronaireOutOfRange,
    StrengthBelowMinimum,
    UniformityBelowMinimum,
)


def test_hvi_with_micronaire_within_range_is_valid():
    hvi = HVIParameters(micronaire=4.2, length=1.16, strength=29.0, uniformity=82.0)
    assert hvi.micronaire == 4.2


def test_hvi_with_micronaire_below_range_raises_error():
    with pytest.raises(MicronaireOutOfRange):
        HVIParameters(micronaire=2.0, length=1.16, strength=29.0, uniformity=82.0)


def test_hvi_with_micronaire_above_range_raises_error():
    with pytest.raises(MicronaireOutOfRange):
        HVIParameters(micronaire=7.5, length=1.16, strength=29.0, uniformity=82.0)


def test_hvi_with_length_at_commercial_minimum_is_valid():
    hvi = HVIParameters(micronaire=4.2, length=1.11, strength=29.0, uniformity=82.0)
    assert hvi.length == 1.11


def test_hvi_with_length_below_commercial_minimum_raises_error():
    with pytest.raises(LengthBelowMinimum):
        HVIParameters(micronaire=4.2, length=1.05, strength=29.0, uniformity=82.0)


def test_hvi_with_strength_at_commercial_minimum_is_valid():
    hvi = HVIParameters(micronaire=4.2, length=1.16, strength=28.0, uniformity=82.0)
    assert hvi.strength == 28.0


def test_hvi_with_strength_below_commercial_minimum_raises_error():
    with pytest.raises(StrengthBelowMinimum):
        HVIParameters(micronaire=4.2, length=1.16, strength=24.0, uniformity=82.0)


def test_hvi_with_uniformity_at_commercial_minimum_is_valid():
    hvi = HVIParameters(micronaire=4.2, length=1.16, strength=29.0, uniformity=80.0)
    assert hvi.uniformity == 80.0


def test_hvi_with_uniformity_below_commercial_minimum_raises_error():
    with pytest.raises(UniformityBelowMinimum):
        HVIParameters(micronaire=4.2, length=1.16, strength=29.0, uniformity=76.0)
