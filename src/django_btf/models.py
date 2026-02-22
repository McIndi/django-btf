from django.db import models


class StoredTask(models.Model):
    result_id = models.CharField(max_length=64, unique=True)
    backend_alias = models.CharField(max_length=64)

    task_path = models.CharField(max_length=512)
    takes_context = models.BooleanField(default=False)
    queue_name = models.CharField(max_length=100)
    priority = models.IntegerField(default=0)

    status = models.CharField(max_length=20, default="READY")

    args = models.JSONField(default=list)
    kwargs = models.JSONField(default=dict)
    return_value = models.JSONField(null=True, blank=True)
    errors = models.JSONField(default=list)
    worker_ids = models.JSONField(default=list)

    run_after = models.DateTimeField(null=True, blank=True)
    enqueued_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    last_attempted_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "queue_name", "run_after", "priority"]),
        ]
