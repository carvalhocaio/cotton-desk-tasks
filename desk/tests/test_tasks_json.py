import pytest
from django.core.management import call_command
from django.urls import reverse

from desk.models import HVIReport
from desk.tasks import summarize_report


@pytest.mark.django_db
def test_tasks_json_lists_recent_tasks_per_queue(client, bale, database_backend):
    report = HVIReport.objects.create(
        bale=bale,
        micronaire="4.20",
        length="1.16",
        strength="29.0",
        uniformity="82.0",
    )

    summarize_report.enqueue(report.id)
    response = client.get(reverse("tasks_json"))

    body = response.json()

    assert response.status_code == 200
    assert len(body["tasks"]) == 1
    task = body["tasks"][0]
    assert task["queue"] == "hvi_reports"
    assert task["task"] == "summarize_report"
    assert task["status"] == "READY"
    assert task["error"] is None


@pytest.mark.django_db(transaction=True)
def test_tasks_json_exposes_the_failure_reason(client, bale, database_backend):
    report = HVIReport.objects.create(
        bale=bale,
        micronaire="2.00",
        length="1.16",
        strength="29.0",
        uniformity="82.0",
    )

    summarize_report.enqueue(report.id)
    call_command("db_worker", queue_name="hvi_reports", batch=True, verbosity=0)
    response = client.get(reverse("tasks_json"))

    body = response.json()
    task = body["tasks"][0]
    assert task["status"] == "FAILED"
    assert task["error"] == "MicronaireOutOfRange"
