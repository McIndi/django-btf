from types import SimpleNamespace
from traceback import format_exception

from django.db import connection, transaction
from django.tasks.base import Task, TaskContext, TaskResultStatus
from django.utils import timezone
from django.utils.json import normalize_json
from django.utils.module_loading import import_string

from .models import StoredTask


def claim_next_task(queue_name="default"):
    now = timezone.now()

    def lock_queryset(queryset):
        if connection.features.has_select_for_update_skip_locked:
            return queryset.select_for_update(skip_locked=True)
        return queryset.select_for_update()

    with transaction.atomic():
        candidate = (
            lock_queryset(StoredTask.objects)
            .filter(status=TaskResultStatus.READY, queue_name=queue_name)
            .filter(run_after__isnull=True)
            .order_by("-priority", "created_at")
            .first()
        )

        if candidate is None:
            candidate = (
                lock_queryset(StoredTask.objects)
                .filter(status=TaskResultStatus.READY, queue_name=queue_name, run_after__lte=now)
                .order_by("-priority", "run_after", "created_at")
                .first()
            )

        if candidate is None:
            return None

        candidate.status = TaskResultStatus.RUNNING
        candidate.started_at = now
        candidate.last_attempted_at = now
        candidate.save(update_fields=["status", "started_at", "last_attempted_at", "updated_at"])
        return candidate


def execute_task_row(row, worker_id):
    imported = import_string(row.task_path)
    func = imported.func if isinstance(imported, Task) else imported

    row.worker_ids = [*row.worker_ids, worker_id]

    try:
        if row.takes_context:
            context = TaskContext(task_result=SimpleNamespace(id=row.result_id))
            value = func(context, *row.args, **row.kwargs)
        else:
            value = func(*row.args, **row.kwargs)

        row.return_value = normalize_json(value)
        row.status = TaskResultStatus.SUCCESSFUL
        row.finished_at = timezone.now()
        row.save(
            update_fields=["return_value", "status", "finished_at", "worker_ids", "updated_at"]
        )
    except BaseException as exc:
        row.errors = [
            *row.errors,
            {
                "exception_class_path": f"{type(exc).__module__}.{type(exc).__qualname__}",
                "traceback": "".join(format_exception(exc)),
            },
        ]
        row.status = TaskResultStatus.FAILED
        row.finished_at = timezone.now()
        row.save(update_fields=["errors", "status", "finished_at", "worker_ids", "updated_at"])
