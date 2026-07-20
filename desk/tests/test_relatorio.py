import pytest
from django.tasks import TaskResultStatus

from desk.models import Fardo, LaudoHVI
from desk.tasks import gerar_relatorio_safra


@pytest.mark.django_db
def test_gerar_relatorio_safra_conta_laudos_validos_e_invalidos():
    fardo_valido = Fardo.objects.create(
        codigo="BR2026000600",
        safra="2025/2026",
        produtor="Fazenda Bom Futuro",
        peso_kg="220.00",
        data_classificacao="2026-04-01",
    )
    fardo_invalido = Fardo.objects.create(
        codigo="BR2026000601",
        safra="2025/2026",
        produtor="Fazenda Bom Futuro",
        peso_kg="215.00",
        data_classificacao="2026-04-01",
    )
    LaudoHVI.objects.create(
        fardo=fardo_valido,
        micronaire="4.20",
        comprimento="1.16",
        resistencia="29.0",
        uniformidade="82.0",
    )
    LaudoHVI.objects.create(
        fardo=fardo_invalido,
        micronaire="2.00",
        comprimento="1.16",
        resistencia="29.0",
        uniformidade="82.0",
    )

    resultado = gerar_relatorio_safra.enqueue("2025/2026")

    assert resultado.status == TaskResultStatus.SUCCESSFUL
    assert resultado.return_value == "Safra 2025/2026: 2 laudos, 1 válido(s), 1 inválido(s)"
