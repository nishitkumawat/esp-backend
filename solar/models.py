from django.db import models

class SolarHourlyData(models.Model):
    device_id = models.CharField(max_length=100)
    voltage = models.FloatField()
    current = models.FloatField()
    power = models.FloatField()
    energy = models.FloatField(default=0.0) # Wh
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device_id', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.device_id} - {self.timestamp} - {self.power}W"

class WashRecord(models.Model):
    WASH_TYPE_CHOICES = [
        ('BEFORE', 'Before Wash'),
        ('AFTER', 'After Wash'),
    ]

    device_id = models.CharField(max_length=100)
    wash_type = models.CharField(max_length=10, choices=WASH_TYPE_CHOICES)
    voltage = models.FloatField()
    current = models.FloatField()
    power = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Optional: Link before/after if needed, but timestamp proximity is usually enough
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.device_id} - {self.wash_type} - {self.timestamp}"
