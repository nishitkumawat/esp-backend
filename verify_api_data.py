from datetime import datetime, timedelta
import random
import os
import django

from django.utils import timezone
# ✅ SET DJANGO SETTINGS MODULE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from solar.models import SolarHourlyData

from solar.models import SolarHourlyData  # your app name is solar

DEVICE_ID = "4CSNISHITKUMAWAT"

def generate_month(year, month):
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    current_day = start_date

    while current_day < end_date:
        base_peak_power = random.randint(2100, 2400)

        for hour in range(6, 19):  # 06:00 to 18:00
            progress = abs(12 - hour)
            power_factor = max(0.2, 1 - (progress / 7))

            power = int(base_peak_power * power_factor * random.uniform(0.95, 1.05))
            voltage = round(random.uniform(28, 40), 1)
            current = round(power / voltage, 1)

            SolarHourlyData.objects.create(
                device_id=DEVICE_ID,
                timestamp=timezone.make_aware(
                    datetime(
                        current_day.year,
                        current_day.month,
                        current_day.day,
                        hour,
                        0
                    )
                ),
                voltage=voltage,
                current=current,
                power=power,
                energy=power
            )

        current_day += timedelta(days=1)

    print(f"Data generated for {year}-{month:02d}")

# Generate December 2025
generate_month(2025, 12)

# Generate January 2026
generate_month(2026, 1)
