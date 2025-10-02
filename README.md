# DjDownloader: Django Download Worker

DjDownloader is a Django app that provides a download worker for downloading files in the background.

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
DJDOWNLOADER_MAX_ATTEMPTS = 10
DJDOWNLOADER_BACKOFF_MAX_TRIES = 5
DJDOWNLOADER_BACKOFF_DELAY = 2
DJDOWNLOADER_WORKER_SLEEP_TIME = 60
```

`mysite/*` is example of installation

## Start Instant Background Download Worker 

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
