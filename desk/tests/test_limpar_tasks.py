import pytest
from django.test import override_settings
from django.urls import reverse
from django_tasks_db.models import DBTaskResult

from desk.tasks import registrar_leitura_indice


@pytest.mark.django_db
def test_limpar_tasks_remove_todo_o_historico(client):
    with override_settings(
        TASKS={
            "default": {
                "BACKEND": "django_tasks_db.DatabaseBackend",
                "QUEUES": ["laudos", "relatorios", "confirmacoes", "precos"],
            }
        }
    ):
        registrar_leitura_indice.enqueue("ICE-CT2", "82.35", "2026-04-28")
        assert DBTaskResult.objects.count() == 1

        resposta = client.post(reverse("limpar_tasks"))

    corpo = resposta.json()
    assert resposta.status_code == 200
    assert corpo["removidas"] == 1
    assert DBTaskResult.objects.count() == 0
