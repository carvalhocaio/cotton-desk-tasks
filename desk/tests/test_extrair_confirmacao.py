from unittest.mock import patch

from django.tasks import TaskResultStatus

from desk.extracao import DadosConfirmacao
from desk.tasks import extrair_confirmacao


def test_extrair_confirmacao_formata_o_resumo_dos_dados_extraidos():
    dados_fake = DadosConfirmacao(
        fardo_codigo="BR2026001000",
        comprador="Têxtil Boa Vista",
        preco_por_kg="6.85",
    )

    with patch("desk.tasks.extrair_dados_confirmacao", return_value=dados_fake):
        resultado = extrair_confirmacao.enqueue(
            "Confirmamos a compra do fardo BR2026001000 pela Têxtil Boa Vista "
            "ao preço de R$ 6,85/kg."
        )

    assert resultado.status == TaskResultStatus.SUCCESSFUL
    assert "BR2026001000" in resultado.return_value
    assert "Têxtil Boa Vista" in resultado.return_value
