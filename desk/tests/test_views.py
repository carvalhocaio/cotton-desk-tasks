from unittest.mock import MagicMock, patch

import pytest
from django.tasks import TaskResultStatus
from django.urls import reverse

from desk.models import HVIReport


@pytest.mark.django_db
def test_post_summarize_report_enqueues_and_returns_task_id(client, bale):
    report = HVIReport.objects.create(
        bale=bale,
        micronaire="4.20",
        length="1.16",
        strength="29.0",
        uniformity="82.0",
    )

    response = client.post(reverse("summarize_report", args=[report.id]))

    assert response.status_code == 202
    assert "task_id" in response.json()


def test_get_task_status_completed_returns_summary(client):
    summary = 'Bale BR2026000500: micronaire 4.2, length 1.16", strength 29.0 gf/tex, uniformity 82.0%'
    fake_result = MagicMock(status=TaskResultStatus.SUCCESSFUL, return_value=summary)

    with patch("desk.views.default_task_backend.get_result", return_value=fake_result):
        response = client.get(reverse("task_status", args=["any-id"]))
    body = response.json()

    assert response.status_code == 200
    assert body == {"status": "completed", "result": summary}


def test_get_task_status_with_invalid_report_returns_failed(client):
    fake_error = MagicMock(exception_class_path="desk.domain.MicronaireOutOfRange")
    fake_result = MagicMock(status=TaskResultStatus.FAILED, errors=[fake_error])

    with patch("desk.views.default_task_backend.get_result", return_value=fake_result):
        response = client.get(reverse("task_status", args=["any-id"]))
    body = response.json()

    assert response.status_code == 422
    assert body["status"] == "failed"
    assert "MicronaireOutOfRange" in body["error"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "task_id",
    ["00000000-0000-0000-0000-000000000000", "not-a-uuid"],
    ids=["absent", "malformed"],
)
def test_get_task_status_with_unknown_id_returns_404(client, database_backend, task_id):
    """Deliberately unmocked.

    django-tasks-db raises django_tasks.exceptions.TaskResultDoesNotExist,
    a different class from Django's same-named one. A mocked backend would
    happily raise whichever class the test picked and prove nothing about
    what the real one does.
    """
    response = client.get(reverse("task_status", args=[task_id]))

    assert response.status_code == 404
