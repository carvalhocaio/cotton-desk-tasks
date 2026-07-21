import pytest
from django.core.management import call_command
from django.tasks import TaskResultStatus, default_task_backend
from django.test import override_settings
from django.urls import reverse

from desk.models import Fardo, LaudoHVI
from desk.tasks import resumir_laudo


@pytest.mark.django_db(transaction=True)
def test_laudo_invalido_falha_de_verdade_com_worker_real(client):
    """Em vez de mockar o TaskResult, roda um worker real
    contra o DatabaseBackend e bate na rota HTTP de verdade.
    """
    fardo = Fardo.objects.create(
        codigo="BR2026000900",
        safra="2025/2026",
        produtor="Fazenda Bom Futuro",
        peso_kg="216.00",
        data_classificacao="2026-04-15",
    )
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
                "QUEUES": ["laudos", "relatorios", "confirmacoes", "precos"],
            }
        }
    ):
        resultado = resumir_laudo.enqueue(laudo.id)
        assert resultado.status == TaskResultStatus.READY

        call_command("db_worker", queue_name="laudos", batch=True, verbosity=0)

        resultado_final = default_task_backend.get_result(resultado.id)
        assert resultado_final.status == TaskResultStatus.FAILED
        assert (
            resultado_final.errors[0].exception_class_path
            == "desk.domain.MicronaireForaDaFaixa"
        )

        resposta = client.get(reverse("status_da_task", args=[resultado.id]))
        corpo = resposta.json()

    assert resposta.status_code == 422
    assert corpo["status"] == "falhou"
    assert "MicronaireForaDaFaixa" in corpo["erro"]
