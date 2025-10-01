import asyncio
import time
from django.core.management.base import BaseCommand
from djdownloader.download import run

class Command(BaseCommand):
    help = 'Starts the download job'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting download job...'))
        try:
            while True:
                asyncio.run(run())
                self.stdout.write(self.style.SUCCESS('Waiting for 60 seconds...'))
                time.sleep(60)
        except (EOFError, KeyboardInterrupt):
            self.stdout.write(self.style.SUCCESS('Stopping download job...'))
