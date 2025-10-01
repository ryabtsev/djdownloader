import aiohttp
import asyncio
import os
import logging
from datetime import datetime

from .models import Task
from .storage import Storage
from .backoff import async_backoff
from django.utils import timezone


logging.basicConfig(level=logging.INFO)


MAX_ATTEMS = 10  # max worker iteration for file 
BACKOFF_MAX_TRIES = 5
BACKOFF_DELAY = 2


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
            logging.info(f"File already downloaded: {file_name}")
            return

        resume_byte_pos = self.storage.get_partial_file_size(partial_path)
        headers = {}
        if resume_byte_pos > 0:
            headers['Range'] = f'bytes={resume_byte_pos}-'
            logging.info(f"Resuming download for {file_name} from byte {resume_byte_pos}")

        try:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                if resume_byte_pos > 0 and response.status == 206:  # Partial Content
                    total_size += resume_byte_pos
                
                if resume_byte_pos >= total_size and total_size != 0:
                    logging.info(f"File already complete, moving: {file_name}")
                    self.storage.move_to_completed(url)
                    return

                mode = 'ab' if resume_byte_pos > 0 else 'wb'
                with open(partial_path, mode) as f:
                    logging.info(f"Starting download: {file_name}")
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                
                if os.path.getsize(partial_path) >= total_size:
                    self.storage.move_to_completed(url)
                else:
                    logging.warning(f"Download incomplete for {file_name}")

        except aiohttp.ClientError as e:
            logging.error(f"Error downloading {file_name} after multiple retries: {e}")
            raise  # Re-raise the exception to be handled by the backoff decorator
        except Exception as e:
            logging.error(f"An unexpected error occurred for {file_name}: {e}")

    async def run(self, tasks: list):
        """
        TODO: add tracking in the Task model (log field)
        """
        async with aiohttp.ClientSession() as session:
            coroutines = []
            for task in tasks:
                url = task.url
                task.status = Task.Status.PROGRESS
                task.file_partial = self.storage.get_file_name(url)
                task.attempts += 1
                await task.asave()

                async def download_wrapper(url):
                    try:
                        await self.download_file(session, url)
                    except aiohttp.ClientError as e:
                        logging.error(f"Failed to download {url} after all retries.")
                        task.datetime_failed = datetime.now()

                        if task.attempts >= MAX_ATTEMS:
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

                coroutines.append(download_wrapper(url))
            await asyncio.gather(*coroutines)


async def run():
    tasks = await Task.objects.get_new_and_failed_tasks()

    storage = Storage()
    requests_handler = RequestsHandler(storage)
    await requests_handler.run(tasks)
