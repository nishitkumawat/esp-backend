from django.db import models


class IotUser(models.Model):
    id = models.AutoField(primary_key=True)
    phone = models.CharField(max_length=20)
    password_hash = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'iot_users'
        managed = False   # VERY IMPORTANT

    def __str__(self):
        return self.name or self.phone


class IotDevice(models.Model):
    id = models.AutoField(primary_key=True)
    device_code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'iot_devices'
        managed = False

    def __str__(self):
        return self.device_code


class IotUserDevice(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        IotUser,
        on_delete=models.DO_NOTHING,
        db_column='user_id'
    )
    device = models.ForeignKey(
        IotDevice,
        on_delete=models.DO_NOTHING,
        db_column='device_id'
    )
    role = models.CharField(max_length=50)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'iot_user_devices'
        managed = False

    def __str__(self):
        return f"{self.user} - {self.device} ({self.role})"


class SGI(models.Model):
    full_name = models.CharField(max_length=255, blank=True, default="")
    company_name = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    contact_number = models.CharField(max_length=20, blank=True, default="")
    requirement = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    
    
# models.py
class ErrorLog(models.Model):
    message = models.TextField()
    traceback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message[:50]