import pytest
from django.test import override_settings


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
            "default": {"BACKEND": "django.tasks.backends.immediate.ImmediateBackend"}
        }
    ):
        yield
