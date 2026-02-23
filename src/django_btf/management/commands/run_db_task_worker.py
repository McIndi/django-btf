import time

from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from django_btf.worker import claim_next_task, execute_task_row


class Command(BaseCommand):
    help = "Run a simple database-backed task worker loop"

    def add_arguments(self, parser):
        parser.add_argument("--queue", default="default")
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--poll-interval", type=float, default=1.0)

    def handle(self, *args, **options):
        queue = options["queue"]
        once = options["once"]
        poll_interval = options["poll_interval"]
        worker_id = get_random_string(32)

        while True:
            row = claim_next_task(queue_name=queue)
            if row is None:
                if once:
                    break
                time.sleep(poll_interval)
                continue

            execute_task_row(row, worker_id=worker_id)

            if once:
                break
