import pytest
from django.urls import reverse

from desk.task_feed import recent_tasks
from desk.tasks import record_index_reading


@pytest.mark.django_db
def test_clear_tasks_removes_the_entire_history(client, database_backend):
    record_index_reading.enqueue("ICE-CT2", "82.35", "2026-04-28")
    assert len(recent_tasks()) == 1

    response = client.post(reverse("clear_tasks"))

    body = response.json()
    assert response.status_code == 200
    assert body["removed"] == 1
    assert recent_tasks() == []
