import pytest
from django.core.management import call_command

from desk.models import HVIReport
from desk.task_feed import clear_history, recent_tasks
from desk.tasks import summarize_report

CARD_KEYS = {
    "id",
    "queue",
    "task",
    "status",
    "error",
    "enqueued_at",
    "started_at",
    "finished_at",
}


def enqueue_report(bale, micronaire="4.20"):
    report = HVIReport.objects.create(
        bale=bale,
        micronaire=micronaire,
        length="1.16",
        strength="29.0",
        uniformity="82.0",
    )
    return summarize_report.enqueue(report.id)


@pytest.mark.django_db
def test_recent_tasks_maps_a_stored_row_onto_the_dashboard_shape(
    bale, database_backend
):
    enqueue_report(bale)

    cards = recent_tasks()

    assert len(cards) == 1
    card = cards[0]
    assert set(card) == CARD_KEYS
    # The package's dotted paths are reduced to leaf names for display.
    assert card["task"] == "summarize_report"
    assert card["queue"] == "hvi_reports"
    assert card["status"] == "READY"
    # Nothing has run yet, so the worker timestamps are still empty.
    assert card["error"] is None
    assert card["enqueued_at"] is not None
    assert card["started_at"] is None
    assert card["finished_at"] is None


@pytest.mark.django_db
def test_recent_tasks_returns_newest_first_and_honours_the_limit(
    bale, database_backend
):
    for _ in range(3):
        enqueue_report(bale)

    cards = recent_tasks(limit=2)

    assert len(cards) == 2
    timestamps = [card["enqueued_at"] for card in cards]
    assert timestamps == sorted(timestamps, reverse=True)


@pytest.mark.django_db(transaction=True)
def test_recent_tasks_exposes_the_failure_reason_as_a_leaf_name(bale, database_backend):
    enqueue_report(bale, micronaire="2.00")
    call_command("db_worker", queue_name="hvi_reports", batch=True, verbosity=0)

    cards = recent_tasks()

    assert cards[0]["status"] == "FAILED"
    assert cards[0]["error"] == "MicronaireOutOfRange"
    assert cards[0]["finished_at"] is not None


@pytest.mark.django_db
def test_clear_history_removes_every_stored_result(bale, database_backend):
    enqueue_report(bale)
    enqueue_report(bale)

    removed = clear_history()

    assert removed == 2
    assert recent_tasks() == []
