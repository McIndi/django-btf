import pytest

from django.tasks import default_task_backend
from django.tasks.base import TaskResultStatus
from django.tasks.exceptions import TaskResultDoesNotExist
from django.core.management import call_command

from django_btf.models import StoredTask
from tests.tasks import add, explode


@pytest.mark.django_db
def test_enqueue_persists_ready_task():
    result = add.enqueue(2, 3)

    assert result.status == TaskResultStatus.READY
    assert result.id

    row = StoredTask.objects.get(result_id=result.id)
    assert row.status == "READY"
    assert row.args == [2, 3]
    assert row.kwargs == {}


@pytest.mark.django_db
def test_get_result_unknown_id_raises():
    with pytest.raises(TaskResultDoesNotExist):
        default_task_backend.get_result("missing-id")

@pytest.mark.django_db
def test_worker_executes_ready_task_successfully():
    result = add.enqueue(10, 7)

    call_command("run_db_task_worker", "--once")

    refreshed = default_task_backend.get_result(result.id)
    assert refreshed.status == TaskResultStatus.SUCCESSFUL
    assert refreshed.return_value == 17


@pytest.mark.django_db
def test_worker_marks_task_failed_with_error():
    result = explode.enqueue()

    call_command("run_db_task_worker", "--once")

    refreshed = default_task_backend.get_result(result.id)
    assert refreshed.status == TaskResultStatus.FAILED
    assert refreshed.errors
    assert "ValueError" in refreshed.errors[0].exception_class_path
