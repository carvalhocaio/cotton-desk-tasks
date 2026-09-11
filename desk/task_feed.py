"""Adapter over `django-tasks-db`'s storage model.

`DBTaskResult` is how the package persists task state, not a public API.
The Tasks Framework itself only exposes `TaskResult` by id, and the
dashboard needs something it has no equivalent for: the last N results
across every queue. Reading the storage model is the pragmatic answer, so
this module is where that bet is contained.

Everything the package owns stays behind this boundary — the import, the
queries, and the column names (`task_path`, `exception_class_path`,
`enqueued_at`). A schema change upstream breaks one module instead of the
view, and the dashboard's JSON contract stays independent of whatever the
package happens to call its columns.
"""

from django.tasks.exceptions import TaskResultDoesNotExist
from django_tasks_db.models import DBTaskResult

try:
    # django-tasks-db is built on the django_tasks backport, which defines
    # its own TaskResultDoesNotExist — same name, no shared ancestry with
    # Django's. Whichever one get_result() raises depends on the configured
    # backend, so callers have to catch both.
    from django_tasks.exceptions import TaskResultDoesNotExist as _BackportNotFound
except ImportError:  # pragma: no cover - only if the backport ever goes away
    _BackportNotFound = TaskResultDoesNotExist

TASK_RESULT_NOT_FOUND = (TaskResultDoesNotExist, _BackportNotFound)

# How far back the dashboard looks. One screen's worth of lanes, not a
# full history — the polling endpoint runs this query every 1.5s per tab.
RECENT_TASK_LIMIT = 50


def recent_tasks(limit: int = RECENT_TASK_LIMIT) -> list[dict]:
    """The most recently enqueued tasks across every queue, newest first."""
    stored = DBTaskResult.objects.order_by("-enqueued_at")[:limit]
    return [_as_card(result) for result in stored]


def clear_history() -> int:
    """Deletes every stored result. Demo shortcut to reset the dashboard."""
    removed, _details = DBTaskResult.objects.all().delete()
    return removed


def _as_card(result) -> dict:
    """Maps one stored row onto the shape the dashboard renders."""
    return {
        "id": str(result.id),
        "queue": result.queue_name,
        "task": _leaf(result.task_path),
        "status": result.status,
        "error": _leaf(result.exception_class_path) or None,
        "enqueued_at": _isoformat(result.enqueued_at),
        "started_at": _isoformat(result.started_at),
        "finished_at": _isoformat(result.finished_at),
    }


def _leaf(dotted_path: str) -> str:
    """Reduces a dotted path to its last segment, for display.

    So `desk.tasks.summarize_report` renders as `summarize_report`.
    """
    return dotted_path.rsplit(".", 1)[-1]


def _isoformat(value):
    # started_at and finished_at are null until the worker picks the task up.
    return value.isoformat() if value else None
