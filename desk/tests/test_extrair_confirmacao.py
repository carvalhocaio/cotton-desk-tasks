from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.tasks import TaskResultStatus

from desk.extracao import DadosConfirmacao
from desk.models import Contrato
from desk.tasks import extrair_confirmacao


@pytest.mark.django_db
def test_extrair_confirmacao_cria_contrato_e_agenda_confirmacao(fardo):
    dados_fake = DadosConfirmacao(
        fardo_codigo=fardo.codigo,
        comprador="Têxtil Boa Vista",
        preco_por_kg="6.85",
    )
    confirmar_contrato_mock = MagicMock()

    with (
        patch("desk.tasks.extrair_dados_confirmacao", return_value=dados_fake),
        patch("desk.tasks.confirmar_contrato", confirmar_contrato_mock),
    ):
        resultado = extrair_confirmacao.enqueue("texto qualquer")

    assert resultado.status == TaskResultStatus.SUCCESSFUL
    contrato = Contrato.objects.get(fardo=fardo)
    assert contrato.comprador == "Têxtil Boa Vista"
    assert contrato.preco_por_kg == Decimal("6.85")
    confirmar_contrato_mock.enqueue.assert_called_once_with(contrato.id)


@pytest.mark.django_db
def test_extrair_confirmacao_com_fardo_inexistente_falha():
    dados_fake = DadosConfirmacao(
        fardo_codigo="BR-CODIGO-INEXISTENTE",
        comprador="Têxtil Boa Vista",
        preco_por_kg="6.85",
    )

    with patch("desk.tasks.extrair_dados_confirmacao", return_value=dados_fake):
        resultado = extrair_confirmacao.enqueue("texto qualquer")

    assert resultado.status == TaskResultStatus.FAILED
    assert resultado.errors[0].exception_class_path == "desk.models.Fardo.DoesNotExist"
