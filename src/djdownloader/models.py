from django.db import models


class TaskManager(models.Manager):
    async def get_new_and_failed_tasks(self):
        return [task async for task in self.filter(status__in=[
            Task.Status.NEW, 
            Task.Status.PROGRESS,
            Task.Status.FAILED,
        ])]


class Task(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        PROGRESS = 'progress', 'In Progress'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'
        FORBIDDEN = 'forbidden', 'Forbidden'

    url = models.URLField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)
    attempts = models.PositiveIntegerField(default=0)
    log = models.TextField(blank=True)
    file_partial = models.FileField(upload_to='partial/', blank=True)
    file_completed = models.FileField(upload_to='completed/', blank=True)
    size_partial = models.BigIntegerField(default=0)
    size_completed = models.BigIntegerField(default=0)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_ready = models.DateTimeField(null=True, blank=True)
    datetime_failed = models.DateTimeField(null=True, blank=True)

    objects = TaskManager()

    def __str__(self):
        return self.url
