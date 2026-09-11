from dataclasses import dataclass, fields
from decimal import Decimal


class InvalidHVIParameter(Exception):
    """Base for any HVI report parameter outside the marketable range."""


class MicronaireOutOfRange(InvalidHVIParameter):
    """Raised when micronaire is outside the marketable range."""


class LengthBelowMinimum(InvalidHVIParameter):
    """Raised when fiber length is below the commercial minimum."""


class StrengthBelowMinimum(InvalidHVIParameter):
    """Raised when fiber strength is below the commercial minimum."""


class UniformityBelowMinimum(InvalidHVIParameter):
    """Raised when uniformity is below the commercial minimum."""


# Decimal, not float: these are instrument readings compared against
# commercial thresholds, and a boundary reading must land on the same side
# of the limit every time. Decimal("1.11") is exactly 1.11; the float 1.11
# is a nearby binary approximation.
MICRONAIRE_MIN = Decimal("3.5")
MICRONAIRE_MAX = Decimal("4.9")
LENGTH_MIN = Decimal("1.11")  # inches (UHML)
STRENGTH_MIN = Decimal("28.0")  # gf/tex
UNIFORMITY_MIN = Decimal("80.0")  # %


def to_reading(value) -> Decimal:
    """Normalizes a reading to Decimal, whatever the caller happens to hold.

    Readings reach the domain as `Decimal` from the model fields and as
    `str` from an uploaded CSV. A `float` goes through `str()` first, so
    4.2 becomes Decimal("4.2") rather than the binary expansion that
    Decimal(4.2) would produce.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    return Decimal(value)


@dataclass(frozen=True)
class HVIParameters:
    """Classification parameters from an HVI (High Volume Instrument) report.

    Pure domain object: does not depend on Django or a database. Every
    parameter is normalized to `Decimal` on construction, so the validation
    below always compares exact decimal quantities.
    """

    micronaire: Decimal
    length: Decimal
    strength: Decimal
    uniformity: Decimal

    def __post_init__(self) -> None:
        for field in fields(self):
            # object.__setattr__ because the dataclass is frozen.
            object.__setattr__(self, field.name, to_reading(getattr(self, field.name)))
        self._validate_micronaire()
        self._validate_length()
        self._validate_strength()
        self._validate_uniformity()

    def _validate_micronaire(self) -> None:
        if not (MICRONAIRE_MIN <= self.micronaire <= MICRONAIRE_MAX):
            raise MicronaireOutOfRange(
                f"micronaire {self.micronaire} outside range "
                f"[{MICRONAIRE_MIN}, {MICRONAIRE_MAX}]"
            )

    def _validate_length(self) -> None:
        if self.length < LENGTH_MIN:
            raise LengthBelowMinimum(
                f'length {self.length}" below the commercial minimum {LENGTH_MIN}"'
            )

    def _validate_strength(self) -> None:
        if self.strength < STRENGTH_MIN:
            raise StrengthBelowMinimum(
                f"strength {self.strength} gf/tex below the commercial minimum "
                f"{STRENGTH_MIN} gf/tex"
            )

    def _validate_uniformity(self) -> None:
        if self.uniformity < UNIFORMITY_MIN:
            raise UniformityBelowMinimum(
                f"uniformity {self.uniformity}% below the commercial minimum "
                f"{UNIFORMITY_MIN}%"
            )
