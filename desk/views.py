import csv
import io
from functools import partial

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.tasks import TaskResultStatus, default_task_backend
from django.views.decorators.csrf import csrf_exempt
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


@csrf_exempt
@require_POST
def summarize_report(request, report_id):
    """Enqueues the summary of an HVI report and returns the task id."""
    result = summarize_report_task.enqueue(report_id)
    return JsonResponse({"task_id": str(result.id)}, status=202)


@require_GET
def task_status(request, task_id):
    """Checks the status of an already-enqueued task."""
    result = default_task_backend.get_result(task_id)
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


@csrf_exempt
@require_POST
def checkout(request):
    """Closes a contract and schedules the confirmation for after the commit."""
    bale = Bale.objects.get(pk=request.POST["bale_id"])
    contract = _close_contract(
        bale, request.POST["buyer"], request.POST["price_per_kg"]
    )
    return JsonResponse({"contract_id": contract.id}, status=201)


@csrf_exempt
@require_POST
def upload_report_batch(request):
    """Receives a CSV of HVI reports, persists each row, and enqueues the summary.

    Demo shortcut: uses `get_or_create` by bale code so the same CSV can be
    resubmitted in manual tests without hitting a uniqueness error — this
    is not the real bale deduplication rule.
    """
    uploaded_file = request.FILES["file"]
    text = io.TextIOWrapper(uploaded_file.file, encoding="utf-8")
    reader = csv.DictReader(text)

    task_ids = []
    created = 0
    for row in reader:
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
        result = summarize_report_task.enqueue(report.id)
        task_ids.append(str(result.id))
        created += 1

    return JsonResponse({"created": created, "task_ids": task_ids}, status=202)


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


@csrf_exempt
@require_POST
def clear_tasks(request):
    """Removes the entire task history — demo shortcut to reset the dashboard."""
    removed, _details = DBTaskResult.objects.all().delete()
    return JsonResponse({"removed": removed})


@csrf_exempt
@require_POST
def demo_report(request):
    """Demo button: enqueues a season report."""
    season = request.POST.get("season", "2025/2026")
    result = generate_season_report.enqueue(season)
    return JsonResponse({"task_id": str(result.id)}, status=202)


@csrf_exempt
@require_POST
def demo_price(request):
    """Demo button: enqueues a price index reading."""
    result = record_index_reading.enqueue("ICE-CT2", "82.35", "2026-04-28")
    return JsonResponse({"task_id": str(result.id)}, status=202)


@csrf_exempt
@require_POST
def demo_contract(request):
    """Demo button: closes a contract using the most recent bale."""
    bale = Bale.objects.order_by("-id").first()
    if bale is None:
        return JsonResponse(
            {"error": "no bale registered — upload a report batch first"},
            status=409,
        )
    contract = _close_contract(bale, "Demo Textile", "6.85")
    return JsonResponse({"contract_id": contract.id}, status=201)


@csrf_exempt
@require_POST
def demo_slow(request):
    """Demo button: enqueues the artificially slow task."""
    result = demo_task.enqueue()
    return JsonResponse({"task_id": str(result.id)}, status=202)


def dashboard(request):
    """Renders the queue dashboard — pure presentation, no business logic."""
    return render(request, "desk/dashboard.html")
