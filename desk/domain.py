from dataclasses import dataclass


class MicronaireForaDaFaixa(Exception):
    """Levantada quando o micronaire de um laudo HVI está fora da faiza comercializável."""


MICRONAIRE_MIN = 3.5
MICRONAIRE_MAX = 4.9


@dataclass(frozen=True)
class HVIParametros:
    """Parâmetros de classificação de um laudo HVI (High Volume Instrument).

    Objeto de domínio puro: não depende de Django nem de banco de dados.
    """

    micronaire: float
    comprimento: float
    resistencia: float
    uniformidade: float

    def __post_init__(self) -> None:
        self._validar_micronaire()

    def _validar_micronaire(self) -> None:
        if not (MICRONAIRE_MIN <= self.micronaire <= MICRONAIRE_MAX):
            raise MicronaireForaDaFaixa(
                f"micronaire {self.micronaire} fora da caixa "
                f"[{MICRONAIRE_MIN}, {MICRONAIRE_MAX}]"
            )
