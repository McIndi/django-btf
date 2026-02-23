# django_btf

A simple database-backed Django Task backend for Django 6.0+.

## Installation

pip install django_btf

## Configuration

Add to your Django project's `settings.py`:

```python
INSTALLED_APPS = [
    "django_btf",
]

TASKS = {
    "default": {
        "BACKEND": "django_btf.backends.db.DatabaseTaskBackend",
    }
}
```

Run migrations:

```bash
python manage.py migrate
```

## Quick Example

Define a task in your app:

```python
from django.tasks import task

@task(queue_name="default")
def send_email(email, subject):
    # Your task logic
    return f"Sent to {email}"
```

Enqueue and retrieve:

```python
result = send_email.enqueue("user@example.com", "Hello")
from django.tasks import default_task_backend
final = default_task_backend.get_result(result.id)
print(final.return_value)
```

## Running the worker

```bash
python manage.py run_db_task_worker
```

Options: --queue, --once, --poll-interval

## License

MIT
