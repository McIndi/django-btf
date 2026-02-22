from django.tasks import task


@task(queue_name="default")
def add(a, b):
    return a + b


@task(queue_name="default")
def explode():
    raise ValueError("boom")
