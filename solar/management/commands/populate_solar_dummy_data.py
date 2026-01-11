import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from solar.models import SolarHourlyData

class Command(BaseCommand):
    help = 'Populates SolarHourlyData with dummy data: 3 months, 4-hour intervals'

    def handle(self, *args, **kwargs):
        device_id = "1CSNISHITKUMAWAT"
        self.stdout.write(f"Clearing and populating data for {device_id}...")

        # Clear ALL data for this device as requested
        SolarHourlyData.objects.filter(device_id=device_id).delete()
        
        end_time = timezone.now()
        # Generate for last 3 months (90 days)
        start_time = end_time - timedelta(days=90)
        
        current_day = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        batch = []
        
        # User requested "gap of 4 hrs". We'll do a simple set of offsets.
        # e.g., 08:00, 12:00, 16:00 covers the main solar windows.
        # If they meant 24h coverage: 0, 4, 8, 12, 16, 20.
        # Given it's Solar, 8-12-16 makes the most sense so we don't have zeros at night.
        hour_offsets = [8, 12, 16] 
        
        while current_day.date() <= end_time.date():
            for hour in hour_offsets:
                # Add some random minute variation? "different time"
                # Let's keep it clean on the hour for graph clarity unless specified.
                timestamp = current_day.replace(hour=hour)
                
                if timestamp > end_time:
                    continue

                # Simulate Power
                # Peak at 12
                if hour == 12:
                    base_power = 2500 # Near Peak
                elif hour in [8, 16]:
                    base_power = 1200 # Morning/Afternoon
                else:
                    base_power = 0
                
                # Randomize
                power = base_power * random.uniform(0.8, 1.1)
                
                # Voltage & Current
                voltage = random.uniform(225, 235) if power > 0 else 0
                current = (power / voltage) if voltage > 0 else 0
                
                # Energy since last reading (4 hours approx) - very rough est
                energy = power * 4 

                batch.append(SolarHourlyData(
                    device_id=device_id,
                    voltage=round(voltage, 2),
                    current=round(current, 2),
                    power=round(power, 2),
                    energy=round(energy, 2),
                    timestamp=timestamp,
                    lat=26.9124, # Jaipur
                    lon=75.7873
                ))
            
            if len(batch) >= 500:
                SolarHourlyData.objects.bulk_create(batch)
                batch = []
                self.stdout.write(f"Generated for {current_day.date()}")
            
            current_day += timedelta(days=1)
            
        if batch:
            SolarHourlyData.objects.bulk_create(batch)

        self.stdout.write(self.style.SUCCESS('Successfully repopulated solar data (3 months, 4hr gaps)'))
