from django.db import models
from .storage import FirmwareStorage

class Device(models.Model):
    device_id = models.CharField(max_length=32, unique=True)
    current_version = models.CharField(max_length=20, default="1.0.0")
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.device_id


class Firmware(models.Model):
    version = models.CharField(max_length=20, unique=True)
    file = models.FileField(upload_to="firmware/", storage=FirmwareStorage())
    checksum = models.CharField(max_length=128)
    released = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.version