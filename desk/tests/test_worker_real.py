import pytest
from django.core.management import call_command
from django.tasks import TaskResultStatus, default_task_backend
from django.test import override_settings
from django.urls import reverse

from desk.models import Bale, HVIReport
from desk.tasks import summarize_report


@pytest.mark.django_db(transaction=True)
def test_invalid_report_fails_for_real_with_a_real_worker(client):
    """Instead of mocking the TaskResult, runs a real worker
    against the DatabaseBackend and hits the real HTTP route.
    """
    bale = Bale.objects.create(
        code="BR2026000900",
        season="2025/2026",
        producer="Bom Futuro Farm",
        weight_kg="216.00",
        classification_date="2026-04-15",
    )
    report = HVIReport.objects.create(
        bale=bale,
        micronaire="2.00",
        length="1.16",
        strength="29.0",
        uniformity="82.0",
    )

    with override_settings(
        TASKS={
            "default": {
                "BACKEND": "django_tasks_db.DatabaseBackend",
                "QUEUES": ["hvi_reports", "season_reports", "confirmations", "prices"],
            }
        }
    ):
        result = summarize_report.enqueue(report.id)
        assert result.status == TaskResultStatus.READY

        call_command("db_worker", queue_name="hvi_reports", batch=True, verbosity=0)

        final_result = default_task_backend.get_result(result.id)
        assert final_result.status == TaskResultStatus.FAILED
        assert (
            final_result.errors[0].exception_class_path
            == "desk.domain.MicronaireOutOfRange"
        )

        response = client.get(reverse("task_status", args=[result.id]))
        body = response.json()

    assert response.status_code == 422
    assert body["status"] == "failed"
    assert "MicronaireOutOfRange" in body["error"]
