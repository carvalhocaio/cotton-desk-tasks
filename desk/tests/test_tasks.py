import pytest
from django.tasks import TaskResultStatus

from desk.models import Contrato, Fardo, LaudoHVI
from desk.tasks import confirmar_contrato, resumir_laudo


@pytest.mark.django_db
def test_resumir_laudo_com_laudo_valido_retorna_resumo_e_status_successful():
    fardo = Fardo.objects.create(
        codigo="BR2026000200",
        safra="2025/2026",
        produtor="Fazenda Bom Futuro",
        peso_kg="218.00",
        data_classificacao="2026-03-20",
    )
    laudo = LaudoHVI.objects.create(
        fardo=fardo,
        micronaire="4.20",
        comprimento="1.16",
        resistencia="29.0",
        uniformidade="82.0",
    )

    resultado = resumir_laudo.enqueue(laudo.id)

    assert resultado.status == TaskResultStatus.SUCCESSFUL
    assert "BR2026000200" in resultado.return_value


@pytest.mark.django_db
def test_confirmar_contrato_com_contrato_valido_retorna_confirmacao_e_status_successful():
    fardo = Fardo.objects.create(
        codigo="BR2026000800",
        safra="2025/2026",
        produtor="Fazenda Bom Futuro",
        peso_kg="219.00",
        data_classificacao="2026-04-10",
    )
    contrato = Contrato.objects.create(
        fardo=fardo,
        comprador="Têxtil Boa Vista",
        preco_por_kg="6.85",
    )

    resultado = confirmar_contrato.enqueue(contrato.id)

    assert resultado.status == TaskResultStatus.SUCCESSFUL
    assert "BR2026000800" in resultado.return_value
    assert "Têxtil Boa Vista" in resultado.return_value
