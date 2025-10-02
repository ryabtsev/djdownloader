# DjDownloader: Django Download Worker

DjDownloader is a Django app that provides a download worker for downloading files in the background.

## Usage

To use the download worker, you need to create a `Task` object in the database. The worker will automatically pick up new tasks and start downloading the files.

You can create a `Task` object programmatically or through the Django admin interface.

## Installation

To install the package, you can use pip:

```bash
pip install djdownloader
```

Add to your `settings.py` file:

```
INSTALLED_APPS = [
    ...
    'djdownloader',
]
```

**Optional settings:**
```
DJDOWNLOADER_WORKER_MAX_ATTEMPTS_FOR_FILE = 10
DJDOWNLOADER_WORKER_SLEEP_TIME_BETWEEN_ITERATIONS = 60
DJDOWNLOADER_WORKER_MAX_PARALLEL_DOWNLOADS = 10  # TBD

DJDOWNLOADER_BACKOFF_MAX_TRIES = 5
DJDOWNLOADER_BACKOFF_DELAY = 2
```

`mysite/*` is example of installation

## Start instant background download worker 

```bash
python manage.py djdownloader
```

## Features

*   **Asynchronous downloads**: Uses `asyncio` and `aiohttp` for simultaneous downloads.
*   **Resumable downloads**: Handles retries using `Range` headers to resume downloads from where they left off.
*   **Backoff mechanism**: Uses a backoff mechanism to handle temporary network interruptions.
*   **Task management**: Uses a Django model to keep track of download tasks, their status, and other details.
*   **Instant Background Download Worker**: Handles downloads tasks.


## Roadmap 

*   Splitting a single file into chunks to download simultaneously.
*   User-facing enhancements.
*   Implement batch limit: DJDOWNLOADER_WORKER_MAX_PARALLEL_DOWNLOADS
