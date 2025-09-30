import aiohttp
import asyncio
import os
import logging
from urllib.parse import urlparse


class Storage:
    """
    TODO: association with django Task model
    """
    def __init__(self, partial_dir='partial', completed_dir='completed'):
        self.partial_dir = partial_dir
        self.completed_dir = completed_dir
        os.makedirs(self.partial_dir, exist_ok=True)
        os.makedirs(self.completed_dir, exist_ok=True)

    def get_file_name(self, url: str) -> str:
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


class RequestsHandler:
    """
    Handles concurrent and resumable file downloads.
    
    TODO: association with django Task model
    TODO: add tracking in the model 
    """
    def __init__(self, storage: Storage):
        self.storage = storage
    
    # TODO: implement backoff decorator
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
                if resume_byte_pos > 0 and response.status == 206: # Partial Content
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
            # TODO: Re-queue for next worker iteration
        except Exception as e:
            logging.error(f"An unexpected error occurred for {file_name}: {e}")

    async def run(self, urls: list[str]):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in urls:
                # The backoff library returns a decorated function.
                # To handle exceptions within the asyncio.gather, we create a wrapper.
                async def download_wrapper(url):
                    try:
                        await self.download_file(session, url)
                    except aiohttp.ClientError as e:
                        logging.error(f"Failed to download {url} after all retries.")
                tasks.append(download_wrapper(url))
            await asyncio.gather(*tasks)

async def main():
    """
    TODO: integration with django Task model

    """
    urls = []
    
    storage = Storage()
    requests_handler = RequestsHandler(storage)
    await requests_handler.run(urls)

if __name__ == "__main__":
    asyncio.run(main())
