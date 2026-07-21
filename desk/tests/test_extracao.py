from pydantic_ai.models.test import TestModel

from desk.extracao import agente_extracao, extrair_dados_confirmacao


def test_extrair_dados_confirmacao_retorna_campos_estruturados():
    saida_simulada = {
        "fardo_codigo": "BR2026001000",
        "comprador": "Têxtil Boa Vista",
        "preco_por_kg": "6.85",
    }

    with agente_extracao.override(model=TestModel(custom_output_args=saida_simulada)):
        dados = extrair_dados_confirmacao(
            "Confirmamos a compra do fardo BR2026001000 pela Têxtil Boa Vista "
            "ao preço de R$ 6,85/kg."
        )

    assert dados.fardo_codigo == "BR2026001000"
    assert dados.comprador == "Têxtil Boa Vista"
    assert dados.preco_por_kg == "6.85"
