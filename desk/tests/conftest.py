import pytest
from django.test import override_settings

from desk.models import Fardo


@pytest.fixture(autouse=True)
def task_immediate_backend():
    """Força o ImmediateBackend durante os testes.

    Em produção o backend é DatabaseBackend, que exige um
    processo `db_worker` ativo para processar a fila. Testes automatizados
    não devem depender de um worker externo rodando em paralelo - por isso
    a suíte roda as tasks in-line, independente do backend de produção.
    """
    with override_settings(
        TASKS={
            "default": {
                "BACKEND": "django.tasks.backends.immediate.ImmediateBackend",
                "QUEUES": ["laudos", "relatorios", "confirmacoes", "precos"],
            }
        }
    ):
        yield


@pytest.fixture
def fardo():
    return Fardo.objects.create(
        codigo="BR2026000500",
        safra="2025/2026",
        produtor="Fazenda Bom Futuro",
        peso_kg="217.00",
        data_classificacao="2026-03-22"
    )
