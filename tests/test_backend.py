import pytest

from django.tasks import default_task_backend
from django.tasks.base import TaskResultStatus
from django.tasks.exceptions import TaskResultDoesNotExist

from django_btf.models import StoredTask
from tests.tasks import add


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
