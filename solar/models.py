from django.db import models
from django.utils import timezone

class SolarHourlyData(models.Model):
    device_id = models.CharField(max_length=100, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    voltage = models.FloatField()
    current = models.FloatField()
    power = models.FloatField()
    energy = models.FloatField()
    # Removed lat/lon as they are now in DeviceLocation

    class Meta:
        indexes = [
            models.Index(fields=['-timestamp', 'device_id']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.device_id} - {self.timestamp}"

class WashRecord(models.Model):
    device_id = models.CharField(max_length=100, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now)
    wash_type = models.CharField(max_length=10, choices=[('BEFORE', 'Before'), ('AFTER', 'After')])
    voltage = models.FloatField()
    current = models.FloatField()
    power = models.FloatField()
    
    # Optional: Link before/after if needed, but timestamp proximity is usually enough
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.device_id} - {self.wash_type} - {self.timestamp}"
class DeviceLocation(models.Model):
    device_id = models.CharField(max_length=100, unique=True, db_index=True)

    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)

    city = models.CharField(max_length=200, default='Unknown')
    state = models.CharField(max_length=200, default='Unknown')
    country = models.CharField(max_length=200, default='', blank=True)
    zip_code = models.CharField(max_length=20, default='', blank=True)
    
    price = models.FloatField(default=5.0)  # Price per unit
    capacity = models.FloatField(default=5.0)  # Total system capacity in kW

    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_updated']

    def __str__(self):
        return f"{self.device_id} - {self.city}, {self.state}"

class SolarAlert(models.Model):
    ALERT_TYPES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('error', 'Error'),
    ]

    device_id = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, default='info')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'device_id']),
        ]

    def __str__(self):
        return f"{self.device_id} - {self.title} ({self.timestamp})"
