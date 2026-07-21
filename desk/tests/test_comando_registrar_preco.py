from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from desk.models import IndicePreco


@pytest.mark.django_db
def test_comando_registrar_preco_enfileira_e_persiste_a_leitura():
    saida = StringIO()

    call_command("registrar_preco", "ICE-CT2", "82.35", "2026-04-15", stdout=saida)

    assert "Enfileirado" in saida.getvalue()
    leitura = IndicePreco.objects.get(codigo="ICE-CT2")
    assert leitura.valor == Decimal("82.35")
