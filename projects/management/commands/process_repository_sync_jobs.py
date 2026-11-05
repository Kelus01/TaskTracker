import time

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from projects.repository_sync import RepositorySyncService


class Command(BaseCommand):
    help = "Process queued GitHub repository synchronization jobs."

    def add_arguments(self, parser):
        parser.add_argument("--poll-interval", type=float, default=1.0)
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        poll_interval = options["poll_interval"]
        if not 0.1 <= poll_interval <= 60:
            raise CommandError("--poll-interval must be between 0.1 and 60 seconds.")

        self.stdout.write("Repository sync worker started.")
        while True:
            close_old_connections()
            try:
                processed = RepositorySyncService.process_next()
            finally:
                close_old_connections()
            if options["once"]:
                return
            if not processed:
                time.sleep(poll_interval)
