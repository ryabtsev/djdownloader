import os
import logging
from django.conf import settings
from urllib.parse import urlparse


class Storage:
    def __init__(
        self, 
        partial_dir=settings.MEDIA_ROOT / 'partial', 
        completed_dir=settings.MEDIA_ROOT / 'completed'
    ):
        self.partial_dir = partial_dir
        self.completed_dir = completed_dir
        os.makedirs(self.partial_dir, exist_ok=True)
        os.makedirs(self.completed_dir, exist_ok=True)

    @staticmethod
    def get_file_name(url: str) -> str:
        return os.path.basename(urlparse(url).path)

    def get_partial_path(self, url: str) -> str:
        return os.path.join(self.partial_dir, self.get_file_name(url))

    def get_completed_path(self, url: str) -> str:
        return os.path.join(self.completed_dir, self.get_file_name(url))

    def get_partial_file_size(self, file_path: str) -> int:
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0

    def move_to_completed(self, url: str):
        partial_path = self.get_partial_path(url)
        completed_path = self.get_completed_path(url)
        os.rename(partial_path, completed_path)
        logging.info(f"Moved completed file: {self.get_file_name(url)}")
