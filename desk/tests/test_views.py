from unittest.mock import MagicMock, patch

import pytest
from django.tasks import TaskResultStatus
from django.urls import reverse

from desk.models import LaudoHVI


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


def test_get_status_da_task_concluida_retorna_resumo(client):
    resumo = 'Fardo BR2026000500: micronaire 4.2, comprimento 1.16", resistência 29.0 gf/tex, uniformidade 82.0%'
    resultado_fake = MagicMock(status=TaskResultStatus.SUCCESSFUL, return_value=resumo)

    with patch(
        "desk.views.default_task_backend.get_result", return_value=resultado_fake
    ):
        resposta = client.get(reverse("status_da_task", args=["qualquer-id"]))
    corpo = resposta.json()

    assert resposta.status_code == 200
    assert corpo == {"status": "concluida", "resultado": resumo}


def test_get_status_da_task_com_laudo_invalido_retorna_falhou(client):
    erro_fake = MagicMock(exception_class_path="desk.domain.MicronaireForaDaFaixa")
    resultado_fake = MagicMock(status=TaskResultStatus.FAILED, errors=[erro_fake])

    with patch(
        "desk.views.default_task_backend.get_result", return_value=resultado_fake
    ):
        resposta = client.get(reverse("status_da_task", args=["qualquer-id"]))
    corpo = resposta.json()

    assert resposta.status_code == 422
    assert corpo["status"] == "falhou"
    assert "MicronaireForaDaFaixa" in corpo["erro"]
