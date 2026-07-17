import pytest

from desk.domain import HVIParametros, MicronaireForaDaFaixa


def test_hvi_com_micronaire_dentro_de_faixa_e_valido():
    hvi = HVIParametros(micronaire=4.2, comprimento=1.16, resistencia=29.0, uniformidade=82.0)

    assert hvi.micronaire == 4.2


def test_hvi_com_micronaire_abaixo_da_faixa_levanta_erro():
    with pytest.raises(MicronaireForaDaFaixa):
        HVIParametros(micronaire=2.0, comprimento=1.16, resistencia=29.0, uniformidade=82.0)


def test_hvi_com_micronaire_acima_da_faixa_levanta_erro():
    with pytest.raises(MicronaireForaDaFaixa):
        HVIParametros(micronaire=7.5, comprimento=1.16, resistencia=29.0, uniformidade=82.0)
