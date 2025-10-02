import asyncio
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from djdownloader.download import run

class Command(BaseCommand):
    help = 'Starts the download job'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting download job...'))
        sleep_time = getattr(settings, 'DJDOWNLOADER_WORKER_SLEEP_TIME', 60)
        try:
            while True:
                asyncio.run(run())
                self.stdout.write(self.style.SUCCESS(f'Waiting for {sleep_time} seconds...'))
                time.sleep(sleep_time)
        except (EOFError, KeyboardInterrupt):
            self.stdout.write(self.style.SUCCESS('Stopping download job...'))
