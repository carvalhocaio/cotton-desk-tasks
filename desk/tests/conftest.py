import pytest
from django.conf import settings
from django.test import override_settings

from desk.models import Bale


@pytest.fixture(autouse=True)
def task_immediate_backend():
    """Forces the ImmediateBackend during tests.

    In production the backend is DatabaseBackend, which requires an
    active `db_worker` process to process the queue. Automated tests
    shouldn't depend on an external worker running in parallel - that's
    why the suite runs tasks inline, regardless of the production
    backend.

    Only the backend is swapped: the queue list is read from the real
    settings so adding a queue there doesn't silently leave the tests
    running against a stale copy.
    """
    with override_settings(
        TASKS={
            "default": {
                "BACKEND": "django.tasks.backends.immediate.ImmediateBackend",
                "QUEUES": settings.TASKS["default"]["QUEUES"],
            }
        }
    ):
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
