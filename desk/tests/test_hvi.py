import pytest

from desk.domain import (
    ComprimentoAbaixoDoMinimo,
    HVIParametros,
    MicronaireForaDaFaixa,
    ResistenciaAbaixoDoMinimo,
    UniformidadeAbaixoDoMinimo,
)


def test_hvi_com_micronaire_dentro_da_faixa_e_valido():
    hvi = HVIParametros(
        micronaire=4.2, comprimento=1.16, resistencia=29.0, uniformidade=82.0
    )
    assert hvi.micronaire == 4.2


def test_hvi_com_micronaire_abaixo_da_faixa_levanta_erro():
    with pytest.raises(MicronaireForaDaFaixa):
        HVIParametros(
            micronaire=2.0, comprimento=1.16, resistencia=29.0, uniformidade=82.0
        )


def test_hvi_com_micronaire_acima_da_faixa_levanta_erro():
    with pytest.raises(MicronaireForaDaFaixa):
        HVIParametros(
            micronaire=7.5, comprimento=1.16, resistencia=29.0, uniformidade=82.0
        )


def test_hvi_com_comprimento_no_minimo_comercial_e_valido():
    hvi = HVIParametros(
        micronaire=4.2, comprimento=1.11, resistencia=29.0, uniformidade=82.0
    )
    assert hvi.comprimento == 1.11


def test_hvi_com_comprimento_abaixo_do_minimo_comercial_levanta_erro():
    with pytest.raises(ComprimentoAbaixoDoMinimo):
        HVIParametros(
            micronaire=4.2, comprimento=1.05, resistencia=29.0, uniformidade=82.0
        )


def test_hvi_com_resistencia_no_minimo_comercial_e_valida():
    hvi = HVIParametros(
        micronaire=4.2, comprimento=1.16, resistencia=28.0, uniformidade=82.0
    )
    assert hvi.resistencia == 28.0


def test_hvi_com_resistencia_abaixo_do_minimo_comercial_levanta_erro():
    with pytest.raises(ResistenciaAbaixoDoMinimo):
        HVIParametros(
            micronaire=4.2, comprimento=1.16, resistencia=24.0, uniformidade=82.0
        )


def test_hvi_com_uniformidade_no_minimo_comercial_e_valida():
    hvi = HVIParametros(
        micronaire=4.2, comprimento=1.16, resistencia=29.0, uniformidade=80.0
    )
    assert hvi.uniformidade == 80.0


def test_hvi_com_uniformidade_abaixo_do_minimo_comercial_levanta_erro():
    with pytest.raises(UniformidadeAbaixoDoMinimo):
        HVIParametros(
            micronaire=4.2, comprimento=1.16, resistencia=29.0, uniformidade=76.0
        )
