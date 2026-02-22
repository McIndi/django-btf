SECRET_KEY = "test-secret-key"
DEBUG = True
USE_TZ = True
TIME_ZONE = "UTC"

INSTALLED_APPS = [
    "django_btf",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "test.sqlite3",
    }
}

TASKS = {
    "default": {
        "BACKEND": "django_btf.backends.db.DatabaseTaskBackend",
    }
}
