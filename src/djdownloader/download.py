import aiohttp
import asyncio
import os
import logging
from datetime import datetime

from .models import Task
from .storage import Storage
from .backoff import async_backoff
from django.utils import timezone
from django.conf import settings


logger = logging.getLogger(__name__)


MAX_ATTEMPTS = getattr(settings, 'DJDOWNLOADER_WORKER_MAX_ATTEMPTS', 10)

BACKOFF_MAX_TRIES = getattr(settings, 'DJDOWNLOADER_BACKOFF_MAX_TRIES', 5)
BACKOFF_DELAY = getattr(settings, 'DJDOWNLOADER_BACKOFF_DELAY', 2)


class RequestsHandler:
    """
    Handles concurrent and resumable file downloads.
    """
    def __init__(self, storage: Storage):
        self.storage = storage
    
    @async_backoff(tries=BACKOFF_MAX_TRIES, delay=BACKOFF_DELAY)
    async def download_file(self, session: aiohttp.ClientSession, url: str):
        partial_path = self.storage.get_partial_path(url)
        file_name = self.storage.get_file_name(url)
        
        if os.path.exists(self.storage.get_completed_path(url)):
            logger.info(f"File already downloaded: {file_name}")
            return

        resume_byte_pos = self.storage.get_partial_file_size(partial_path)
        headers = {}
        if resume_byte_pos > 0:
            headers['Range'] = f'bytes={resume_byte_pos}-'
            logger.info(f"Resuming download for {file_name} from byte {resume_byte_pos}")

        try:
            timeout = aiohttp.ClientTimeout(sock_read=15)
            async with session.get(url, headers=headers, timeout=timeout) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                if resume_byte_pos > 0 and response.status == 206:  # Partial Content
                    total_size += resume_byte_pos
                
                if resume_byte_pos >= total_size and total_size != 0:
                    logger.info(f"File already complete, moving: {file_name}")
                    self.storage.move_to_completed(url)
                    return

                mode = 'ab' if resume_byte_pos > 0 else 'wb'
                with open(partial_path, mode) as f:
                    logger.info(f"Starting download: {file_name}")
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                
                if os.path.getsize(partial_path) >= total_size:
                    self.storage.move_to_completed(url)
                else:
                    logger.warning(f"Download incomplete for {file_name}")

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Error downloading {file_name} after multiple retries: {e}")
            raise  # Re-raise the exception to be handled by the backoff decorator
        except Exception as e:
            logger.error(f"An unexpected error occurred for {file_name}: {e}")

    async def run(self, tasks: list):
        """
        TODO: add tracking in the Task model (log field)
        """
        async def download_wrapper(task):
            url = task.url
            task.status = Task.Status.PROGRESS
            task.file_partial = self.storage.get_file_name(url)
            task.attempts += 1
            await task.asave()
            
            try:
                await self.download_file(session, url)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error(f"Failed to download {url} after all retries.")
                task.datetime_failed = datetime.now()

                if task.attempts >= MAX_ATTEMPTS:
                    task.status = Task.Status.FORBIDDEN
                else:
                    task.status = Task.Status.FAILED
            else:
                task.status = Task.Status.READY
                task.datetime_ready = timezone.now()
                task.file_partial = ''
                task.file_completed = self.storage.get_file_name(url)
            finally:
                await task.asave()
    
        async with aiohttp.ClientSession() as session:
            coroutines = []
            for task in tasks:
                coroutines.append(download_wrapper(task))
            await asyncio.gather(*coroutines)


async def run():
    tasks = await Task.objects.get_new_and_failed_tasks()

    storage = Storage()
    requests_handler = RequestsHandler(storage)
    await requests_handler.run(tasks)