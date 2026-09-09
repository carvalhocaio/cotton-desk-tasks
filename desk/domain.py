from dataclasses import dataclass


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


MICRONAIRE_MIN = 3.5
MICRONAIRE_MAX = 4.9
LENGTH_MIN = 1.11  # inches (UHML)
STRENGTH_MIN = 28.0  # gf/tex
UNIFORMITY_MIN = 80.0  # %


@dataclass(frozen=True)
class HVIParameters:
    """Classification parameters from an HVI (High Volume Instrument) report.

    Pure domain object: does not depend on Django or a database.
    """

    micronaire: float
    length: float
    strength: float
    uniformity: float

    def __post_init__(self) -> None:
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
