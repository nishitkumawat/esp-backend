import os
import django
import json
from django.db import connection

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from solar.models import ExtraDevice
from iot.models import IotDevice, IotUser, IotUserDevice

def test_extra_device_override():
    print("--- Starting ExtraDevice Override Test ---")
    
    device_code = "TEST001"
    to_consider = "OC"
    
    # 1. Ensure test device doesn't exist
    ExtraDevice.objects.filter(device_id=device_code).delete()
    
    # 2. Check type without override
    from iot.views import get_device_type
    initial_type = get_device_type(device_code)
    print(f"Initial type for {device_code}: {initial_type} (Expected: SM)")
    
    # 3. Add override
    ExtraDevice.objects.create(device_id=device_code, to_consider=to_consider)
    print(f"Added override: {device_code} -> {to_consider}")
    
    # 4. Check type with override
    new_type = get_device_type(device_code)
    print(f"New type for {device_code}: {new_type} (Expected: {to_consider})")
    
    if new_type == to_consider:
        print("✅ Override logic verified successfully!")
    else:
        print("❌ Override logic failed!")

    # Cleanup
    ExtraDevice.objects.filter(device_id=device_code).delete()
    print("--- Test Completed ---")

if __name__ == "__main__":
    test_extra_device_override()
