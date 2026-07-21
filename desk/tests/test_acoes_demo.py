import pytest
from django.urls import reverse

from desk.models import Contrato, IndicePreco


@pytest.mark.django_db
def test_relatorio_teste_enfileira_gerar_relatorio_safra(client):
    resposta = client.post(reverse("relatorio_teste"), {"safra": "2025/2026"})

    assert resposta.status_code == 202
    assert "task_id" in resposta.json()


@pytest.mark.django_db
def test_preco_teste_enfileira_registrar_leitura_indice(client):
    resposta = client.post(reverse("preco_teste"))

    assert resposta.status_code == 202
    assert "task_id" in resposta.json()
    assert IndicePreco.objects.filter(codigo="ICE-CT2").exists()


@pytest.mark.django_db
def test_contrato_teste_fecha_contrato_com_fardo_mais_recente(client, fardo):
    resposta = client.post(reverse("contrato_teste"))

    assert resposta.status_code == 201
    assert Contrato.objects.filter(fardo=fardo).exists()


@pytest.mark.django_db
def test_contrato_teste_sem_fardo_disponivel_retorna_erro(client):
    resposta = client.post(reverse("contrato_teste"))

    assert resposta.status_code == 409
    assert "erro" in resposta.json()
