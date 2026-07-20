from dataclasses import dataclass


class ParametroHVIInvalido(Exception):
    """Base para qualquer parâmetro de laudo HVI fora da faixa comercializável."""


class MicronaireForaDaFaixa(ParametroHVIInvalido):
    """Levantada quando o micronaire está fora da faixa comercializável."""


class ComprimentoAbaixoDoMinimo(ParametroHVIInvalido):
    """Levantada quando o comprimento de fibra está abaixo do mínimo comercial."""


class ResistenciaAbaixoDoMinimo(ParametroHVIInvalido):
    """Levantada quando a resistência de fibra está abaixo do mínimo comercial."""


class UniformidadeAbaixoDoMinimo(ParametroHVIInvalido):
    """Levantada quando a uniformidade está abaixo do mínimo comercial."""


MICRONAIRE_MIN = 3.5
MICRONAIRE_MAX = 4.9
COMPRIMENTO_MIN = 1.11  # polegadas (UHML)
RESISTENCIA_MIN = 28.0  # gf/tex
UNIFORMIDADE_MIN = 80.0  # %


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
        self._validar_comprimento()
        self._validar_resistencia()
        self._validar_uniformidade()

    def _validar_micronaire(self) -> None:
        if not (MICRONAIRE_MIN <= self.micronaire <= MICRONAIRE_MAX):
            raise MicronaireForaDaFaixa(
                f"micronaire {self.micronaire} fora da faixa "
                f"[{MICRONAIRE_MIN}, {MICRONAIRE_MAX}]"
            )

    def _validar_comprimento(self) -> None:
        if self.comprimento < COMPRIMENTO_MIN:
            raise ComprimentoAbaixoDoMinimo(
                f"comprimento {self.comprimento}\" abaixo do mínimo comercial "
                f"{COMPRIMENTO_MIN}\""
            )

    def _validar_resistencia(self) -> None:
        if self.resistencia < RESISTENCIA_MIN:
            raise ResistenciaAbaixoDoMinimo(
                f"resistência {self.resistencia} gf/tex abaixo do mínimo comercial "
                f"{RESISTENCIA_MIN} gf/tex"
            )

    def _validar_uniformidade(self) -> None:
        if self.uniformidade < UNIFORMIDADE_MIN:
            raise UniformidadeAbaixoDoMinimo(
                f"uniformidade {self.uniformidade}% abaixo do mínimo comercial "
                f"{UNIFORMIDADE_MIN}%"
            )
