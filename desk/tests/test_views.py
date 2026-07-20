import pytest
from django.urls import reverse

from desk.models import Fardo, LaudoHVI


@pytest.fixture
def fardo():
    return Fardo.objects.create(
        codigo="BR2026000500",
        safra="2025/2026",
        produtor="Fazenda Bom Futuro",
        peso_kg="217.00",
        data_classificacao="2026-03-22",
    )

@pytest.mark.django_db
def test_post_resumir_laudo_enfileira_e_retorna_task_id(client, fardo):
    laudo = LaudoHVI.objects.create(
        fardo=fardo,
        micronaire="4.20",
        comprimento="1.16",
        resistencia="29.0",
        uniformidade="82.0",
    )

    resposta = client.post(reverse("resumir_laudo", args=[laudo.id]))

    assert resposta.status_code == 202
    assert "task_id" in resposta.json()


@pytest.mark.django_db
def test_get_status_da_task_concluida_retorna_resumo(client, fardo):
    laudo = LaudoHVI.objects.create(
        fardo=fardo,
        micronaire="4.20",
        comprimento="1.16",
        resistencia="29.0",
        uniformidade="82.0",
    )
    task_id = client.post(reverse("resumir_laudo", args=[laudo.id])).json()["task_id"]

    resposta = client.get(reverse("status_da_task", args=[task_id]))
    corpo = resposta.json()

    assert resposta.status_code == 200
    assert corpo["status"] == "concluida"
    assert "BR2026000500" in corpo["resultado"]


@pytest.mark.django_db
def test_get_status_da_task_com_laudo_invalido_retorna_falhou(client, fardo):
    laudo = LaudoHVI.objects.create(
        fardo=fardo,
        micronaire="2.00",
        comprimento="1.16",
        resistencia="29.0",
        uniformidade="82.0",
    )
    task_id = client.post(reverse("status_da_task", args=[laudo.id])).json()["task_id"]

    resposta = client.get(reverse("status_da_task", args=[task_id]))
    corpo = resposta.json()

    assert resposta.status_code == 422
    assert corpo["status"] == "falhou"
    assert "MicronaireForaDaFaixa" in corpo["erro"]
