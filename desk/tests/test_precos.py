from decimal import Decimal

import pytest
from django.tasks import TaskResultStatus

from desk.models import IndicePreco
from desk.tasks import registrar_leitura_indice


def test_enqueue_com_decimal_bruto_falha_na_serializacao():
    """Documenta o gotcha: Decimal não sobrevive à serialização JSON do enqueue."""
    with pytest.raises(TypeError):
        registrar_leitura_indice.enqueue("ICE-CT2", Decimal("82.35"), "2026-04-10")


@pytest.mark.django_db
def test_registrar_leitura_indice_com_valor_como_string_persiste_como_decimal():
    resultado = registrar_leitura_indice.enqueue("ICE-CT2", "82.35", "2026-04-10")

    assert resultado.status == TaskResultStatus.SUCCESSFUL
    leitura = IndicePreco.objects.get(codigo="ICE-CT2")
    assert leitura.valor == Decimal("82.35")
