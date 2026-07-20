import pytest

from desk.domain import HVIParametros, MicronaireForaDaFaixa
from desk.models import Fardo, LaudoHVI


@pytest.mark.django_db
def test_laudo_hvi_valido_converte_para_hviparametros():
    fardo = Fardo.objects.create(
        codigo="BR2026000123",
        safra="2025/2026",
        produtor="Fazenda Bom Futuro",
        peso_kg="220.50",
        data_classificacao="2026-03-15",
    )
    laudo = LaudoHVI.objects.create(
        fardo=fardo,
        micronaire="4.20",
        comprimento="1.16",
        resistencia="29.0",
        uniformidade="82.0",
    )

    parametros = laudo.to_dominio()

    assert parametros == HVIParametros(
        micronaire=4.2, comprimento=1.16, resistencia=29.0, uniformidade=82.0
    )


@pytest.mark.django_db
def test_laudo_hvi_com_micronaire_invalido_salva_mas_levanta_erro_ao_converter():
    fardo = Fardo.objects.create(
        codigo="BR2026000124",
        safra="2025/2026",
        produtor="Fazenda Bom Futuro",
        peso_kg="215.00",
        data_classificacao="2026-03-15",
    )
    laudo = LaudoHVI.objects.create(
        fardo=fardo,
        micronaire="2.00",
        comprimento="1.16",
        resistencia="29.0",
        uniformidade="82.0",
    )

    with pytest.raises(MicronaireForaDaFaixa):
        laudo.to_dominio()
