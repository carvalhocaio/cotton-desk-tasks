import pytest
from django.test import override_settings
from django.urls import reverse
from django_tasks_db.models import DBTaskResult

from desk.tasks import record_index_reading


@pytest.mark.django_db
def test_clear_tasks_removes_the_entire_history(client):
    with override_settings(
        TASKS={
            "default": {
                "BACKEND": "django_tasks_db.DatabaseBackend",
                "QUEUES": ["hvi_reports", "season_reports", "confirmations", "prices"],
            }
        }
    ):
        record_index_reading.enqueue("ICE-CT2", "82.35", "2026-04-28")
        assert DBTaskResult.objects.count() == 1

        response = client.post(reverse("clear_tasks"))

    body = response.json()
    assert response.status_code == 200
    assert body["removed"] == 1
    assert DBTaskResult.objects.count() == 0
