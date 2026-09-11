import pytest
from django.conf import settings
from django.test import override_settings

from desk.models import Bale


def _backend(dotted_path):
    """override_settings for one backend, reusing the real queue list.

    Reading QUEUES from settings means adding a queue there doesn't leave
    the tests running against a stale copy of the list.
    """
    return override_settings(
        TASKS={
            "default": {
                "BACKEND": dotted_path,
                "QUEUES": settings.TASKS["default"]["QUEUES"],
            }
        }
    )


@pytest.fixture(autouse=True)
def task_immediate_backend():
    """Forces the ImmediateBackend during tests.

    In production the backend is DatabaseBackend, which requires an
    active `db_worker` process to process the queue. Automated tests
    shouldn't depend on an external worker running in parallel - that's
    why the suite runs tasks inline, regardless of the production
    backend.

    Tests that do need stored rows take the `database_backend` fixture,
    which overrides this one.
    """
    with _backend("django.tasks.backends.immediate.ImmediateBackend"):
        yield


@pytest.fixture
def database_backend():
    """Swaps the DatabaseBackend in, overriding the autouse fixture above.

    Running tasks inline never writes a TaskResult row, so anything that
    asserts on stored state — the dashboard feed, a real worker run,
    checking a task's status by id — needs the real backend instead.
    """
    with _backend("django_tasks_db.DatabaseBackend"):
        yield


@pytest.fixture
def bale():
    return Bale.objects.create(
        code="BR2026000500",
        season="2025/2026",
        producer="Bom Futuro Farm",
        weight_kg="217.00",
        classification_date="2026-03-22",
    )
