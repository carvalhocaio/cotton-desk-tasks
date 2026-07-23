import pytest
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from desk.models import LaudoHVI
from desk.tasks import resumir_laudo


@pytest.mark.django_db
def test_tasks_json_lista_tasks_recentes_por_fila(client, fardo):
    laudo = LaudoHVI.objects.create(
        fardo=fardo,
        micronaire="4.20",
        comprimento="1.16",
        resistencia="29.0",
        uniformidade="82.0",
    )

    with override_settings(
        TASKS={
            "default": {
                "BACKEND": "django_tasks_db.DatabaseBackend",
                "QUEUES": ["laudos", "relatorios", "confirmacoes", "precos", "demo"],
            }
        }
    ):
        resumir_laudo.enqueue(laudo.id)
        resposta = client.get(reverse("tasks_json"))

    corpo = resposta.json()

    assert resposta.status_code == 200
    assert len(corpo["tasks"]) == 1
    tarefa = corpo["tasks"][0]
    assert tarefa["fila"] == "laudos"
    assert tarefa["tarefa"] == "resumir_laudo"
    assert tarefa["status"] == "READY"
    assert tarefa["erro"] is None


@pytest.mark.django_db(transaction=True)
def test_tasks_json_expoe_o_motivo_da_falha(client, fardo):
    laudo = LaudoHVI.objects.create(
        fardo=fardo,
        micronaire="2.00",
        comprimento="1.16",
        resistencia="29.0",
        uniformidade="82.0",
    )

    with override_settings(
        TASKS={
            "default": {
                "BACKEND": "django_tasks_db.DatabaseBackend",
                "QUEUES": ["laudos", "relatorios", "confirmacoes", "precos", "demo"],
            }
        }
    ):
        resumir_laudo.enqueue(laudo.id)
        call_command("db_worker", queue_name="laudos", batch=True, verbosity=0)
        resposta = client.get(reverse("tasks_json"))

    corpo = resposta.json()
    tarefa = corpo["tasks"][0]
    assert tarefa["status"] == "FAILED"
    assert tarefa["erro"] == "MicronaireForaDaFaixa"
