from asgiref.sync import sync_to_async

from django.tasks.backends.base import BaseTaskBackend
from django.tasks.base import Task, TaskError, TaskResult, TaskResultStatus
from django.tasks.exceptions import TaskResultDoesNotExist
from django.tasks.signals import task_enqueued
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.module_loading import import_string

from django_btf.models import StoredTask


class DatabaseTaskBackend(BaseTaskBackend):
    supports_defer = True
    supports_async_task = True
    supports_get_result = True
    supports_priority = True

    def _row_to_result(self, row):
        imported = import_string(row.task_path)
        func = imported.func if isinstance(imported, Task) else imported
        task_obj = Task(
            func=func,
            backend=row.backend_alias,
            queue_name=row.queue_name,
            priority=row.priority,
            run_after=row.run_after,
            takes_context=row.takes_context,
        )

        result = TaskResult(
            task=task_obj,
            id=row.result_id,
            status=TaskResultStatus(row.status),
            enqueued_at=row.enqueued_at,
            started_at=row.started_at,
            last_attempted_at=row.last_attempted_at,
            finished_at=row.finished_at,
            args=row.args,
            kwargs=row.kwargs,
            backend=row.backend_alias,
            errors=[TaskError(**error) for error in row.errors],
            worker_ids=row.worker_ids,
        )

        if row.status == TaskResultStatus.SUCCESSFUL and row.return_value is not None:
            object.__setattr__(result, "_return_value", row.return_value)

        return result

    def enqueue(self, task, args, kwargs):
        self.validate_task(task)

        result_id = get_random_string(32)
        enqueued_at = timezone.now()

        row = StoredTask.objects.create(
            result_id=result_id,
            backend_alias=self.alias,
            task_path=f"{task.func.__module__}.{task.func.__qualname__}",
            takes_context=task.takes_context,
            queue_name=task.queue_name,
            priority=task.priority,
            status=TaskResultStatus.READY,
            args=list(args),
            kwargs=kwargs,
            run_after=task.run_after,
            enqueued_at=enqueued_at,
            worker_ids=[],
            errors=[],
        )

        result = self._row_to_result(row)
        task_enqueued.send(type(self), task_result=result)
        return result

    async def aenqueue(self, task, args, kwargs):
        return await sync_to_async(self.enqueue, thread_sensitive=True)(task, args, kwargs)

    def get_result(self, result_id):
        try:
            row = StoredTask.objects.get(result_id=result_id)
        except StoredTask.DoesNotExist:
            raise TaskResultDoesNotExist(result_id) from None

        return self._row_to_result(row)

    async def aget_result(self, result_id):
        return await sync_to_async(self.get_result, thread_sensitive=True)(result_id)
