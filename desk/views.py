import csv
import io
from decimal import Decimal, InvalidOperation
from functools import partial

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.tasks import TaskResultStatus, default_task_backend
from django.tasks.exceptions import TaskResultDoesNotExist
from django.views.decorators.http import require_GET, require_POST
from django_tasks_db.models import DBTaskResult

from desk.models import Bale, Contract, HVIReport
from desk.tasks import (
    confirm_contract,
    demo_task,
    generate_season_report,
    record_index_reading,
)
from desk.tasks import summarize_report as summarize_report_task

# Columns the batch upload expects, in the order documented in the README and
# offered by the dashboard's "download sample CSV" button.
CSV_COLUMNS = (
    "code",
    "season",
    "producer",
    "weight_kg",
    "classification_date",
    "micronaire",
    "length",
    "strength",
    "uniformity",
)

# Upper bound on a single batch. Django's DATA_UPLOAD_MAX_MEMORY_SIZE does not
# apply to file uploads, so without this one request could enqueue unbounded work.
MAX_CSV_ROWS = 1000


class BatchRejected(Exception):
    """Batch-level refusal raised from inside the upload's transaction.

    It has to be an exception, not an early return: returning out of a
    `transaction.atomic()` block leaves it without an exception to roll back
    on, so the rows written before the refusal would commit.
    """


def _bad_request(message):
    return JsonResponse({"error": message}, status=400)


@require_POST
def summarize_report(request, report_id):
    """Enqueues the summary of an HVI report and returns the task id."""
    result = summarize_report_task.enqueue(report_id)
    return JsonResponse({"task_id": str(result.id)}, status=202)


@require_GET
def task_status(request, task_id):
    """Checks the status of an already-enqueued task."""
    try:
        result = default_task_backend.get_result(task_id)
    except (TaskResultDoesNotExist, ValueError):
        # ValueError covers a task_id that isn't even a well-formed UUID.
        return JsonResponse({"error": "unknown task id"}, status=404)
    result.refresh()

    if result.status == TaskResultStatus.SUCCESSFUL:
        return JsonResponse({"status": "completed", "result": result.return_value})

    if result.status == TaskResultStatus.FAILED:
        error = result.errors[0].exception_class_path
        return JsonResponse({"status": "failed", "error": error}, status=422)

    return JsonResponse({"status": "pending"})


def _close_contract(bale, buyer, price_per_kg):
    """Creates the contract and schedules the confirmation for after the commit.

    Shared between the `checkout` view (real flow) and `demo_contract`
    (dashboard demo button).
    """
    with transaction.atomic():
        contract = Contract.objects.create(
            bale=bale, buyer=buyer, price_per_kg=price_per_kg
        )
        transaction.on_commit(partial(confirm_contract.enqueue, contract.id))
    return contract


@require_POST
def checkout(request):
    """Closes a contract and schedules the confirmation for after the commit."""
    bale_id = request.POST.get("bale_id")
    buyer = request.POST.get("buyer")
    raw_price = request.POST.get("price_per_kg")

    missing = [
        name
        for name, value in (
            ("bale_id", bale_id),
            ("buyer", buyer),
            ("price_per_kg", raw_price),
        )
        if not value
    ]
    if missing:
        return _bad_request(f"missing field(s): {', '.join(missing)}")

    try:
        price_per_kg = Decimal(raw_price)
    except InvalidOperation:
        return _bad_request(f"price_per_kg {raw_price!r} is not a valid decimal")

    bale = get_object_or_404(Bale, pk=bale_id)
    contract = _close_contract(bale, buyer, price_per_kg)
    return JsonResponse({"contract_id": contract.id}, status=201)


@require_POST
def upload_report_batch(request):
    """Receives a CSV of HVI reports, persists each row, and enqueues the summary.

    The whole batch is one transaction: a malformed row on line 40 must not
    leave the first 39 persisted. The summaries are scheduled with
    `transaction.on_commit` for the same reason `_close_contract` does it — a
    worker must never pick up a report the database hasn't committed yet.

    Demo shortcut: uses `get_or_create` by bale code so the same CSV can be
    resubmitted in manual tests without hitting a uniqueness error — this
    is not the real bale deduplication rule.
    """
    uploaded_file = request.FILES.get("file")
    if uploaded_file is None:
        return _bad_request("missing file")

    text = io.TextIOWrapper(uploaded_file.file, encoding="utf-8")
    reader = csv.DictReader(text)

    missing_columns = [c for c in CSV_COLUMNS if c not in (reader.fieldnames or ())]
    if missing_columns:
        return _bad_request(f"missing CSV column(s): {', '.join(missing_columns)}")

    report_ids = []
    line = 1  # header; bumped per row, and reported if one blows up
    try:
        with transaction.atomic():
            for row in reader:
                line += 1
                if len(report_ids) >= MAX_CSV_ROWS:
                    # Raise rather than return: returning out of an atomic
                    # block exits it without an exception, which commits — the
                    # rejected batch would be persisted and enqueued anyway.
                    raise BatchRejected(
                        f"batch exceeds the {MAX_CSV_ROWS}-row limit — split the file"
                    )
                bale, _bale_created = Bale.objects.get_or_create(
                    code=row["code"],
                    defaults={
                        "season": row["season"],
                        "producer": row["producer"],
                        "weight_kg": row["weight_kg"],
                        "classification_date": row["classification_date"],
                    },
                )
                report = HVIReport.objects.create(
                    bale=bale,
                    micronaire=row["micronaire"],
                    length=row["length"],
                    strength=row["strength"],
                    uniformity=row["uniformity"],
                )
                report_ids.append(report.id)
                transaction.on_commit(partial(summarize_report_task.enqueue, report.id))
    except BatchRejected as exc:
        return _bad_request(str(exc))
    except (ValidationError, InvalidOperation, ValueError, TypeError) as exc:
        # A row whose values don't fit the model fields (a non-numeric
        # micronaire, an unparseable date). The atomic block already rolled the
        # whole batch back; report which line broke it.
        return _bad_request(f"invalid value on line {line}: {exc}")

    return JsonResponse(
        {"created": len(report_ids), "report_ids": report_ids}, status=202
    )


@require_GET
def tasks_json(request):
    """Lists the most recent tasks per queue, for the dashboard to consume via polling."""
    tasks = DBTaskResult.objects.order_by("-enqueued_at")[:50]
    data = [
        {
            "id": str(t.id),
            "queue": t.queue_name,
            "task": t.task_path.rsplit(".", 1)[-1],
            "status": t.status,
            "error": t.exception_class_path.rsplit(".", 1)[-1] or None,
            "enqueued_at": t.enqueued_at.isoformat() if t.enqueued_at else None,
            "started_at": t.started_at.isoformat() if t.started_at else None,
            "finished_at": t.finished_at.isoformat() if t.finished_at else None,
        }
        for t in tasks
    ]
    return JsonResponse({"tasks": data})


@require_POST
def clear_tasks(request):
    """Removes the entire task history — demo shortcut to reset the dashboard."""
    removed, _details = DBTaskResult.objects.all().delete()
    return JsonResponse({"removed": removed})


@require_POST
def demo_report(request):
    """Demo button: enqueues a season report."""
    season = request.POST.get("season", "2025/2026")
    result = generate_season_report.enqueue(season)
    return JsonResponse({"task_id": str(result.id)}, status=202)


@require_POST
def demo_price(request):
    """Demo button: enqueues a price index reading."""
    result = record_index_reading.enqueue("ICE-CT2", "82.35", "2026-04-28")
    return JsonResponse({"task_id": str(result.id)}, status=202)


@require_POST
def demo_contract(request):
    """Demo button: closes a contract using the most recent bale."""
    bale = Bale.objects.order_by("-id").first()
    if bale is None:
        return JsonResponse(
            {"error": "no bale registered — upload a report batch first"},
            status=409,
        )
    contract = _close_contract(bale, "Demo Textile", Decimal("6.85"))
    return JsonResponse({"contract_id": contract.id}, status=201)


@require_POST
def demo_slow(request):
    """Demo button: enqueues the artificially slow task."""
    result = demo_task.enqueue()
    return JsonResponse({"task_id": str(result.id)}, status=202)


def dashboard(request):
    """Renders the queue dashboard — pure presentation, no business logic."""
    return render(request, "desk/dashboard.html")
