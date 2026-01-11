from django.core.management.base import BaseCommand
import random
from datetime import datetime, timedelta, time
from django.utils import timezone
from solar.models import SolarHourlyData 

class Command(BaseCommand):
    help = 'Executes user provided dummy data script'

    def handle(self, *args, **options):
        DEVICE_ID = "1CSNISHITKUMAWAT"
        LAT = 23.0225
        LON = 72.5714

        # Pre-emptive clear based on previous context, to ensure clean graph
        SolarHourlyData.objects.filter(device_id=DEVICE_ID).delete()
        self.stdout.write(f"Cleared existing data for {DEVICE_ID}")

        today = timezone.now().date()
        start_date = today - timedelta(days=90)

        objects = []

        for day in range(90):
            date = start_date + timedelta(days=day)

            # 12–13 random entries per day
            entries_count = random.randint(12, 13)

            used_minutes = set()
            daily_energy = 0.0

            for _ in range(entries_count):
                # Random time between 6 AM and 7 PM
                hour = random.randint(6, 18)
                minute = random.randint(0, 59)

                # Avoid same timestamp
                while (hour, minute) in used_minutes:
                    minute = random.randint(0, 59)

                used_minutes.add((hour, minute))

                ts = timezone.make_aware(
                    datetime.combine(date, time(hour, minute))
                )

                voltage = round(random.uniform(18.0, 38.0), 2)
                current = round(random.uniform(0.5, 8.0), 2)
                power = round(voltage * current, 2)

                # assume ~1 hour gap equivalent
                energy = round(power * random.uniform(0.7, 1.1), 2)
                daily_energy += energy

                objects.append(
                    SolarHourlyData(
                        device_id=DEVICE_ID,
                        voltage=voltage,
                        current=current,
                        power=power,
                        energy=daily_energy,
                        lat=LAT,
                        lon=LON,
                        timestamp=ts
                    )
                )

        SolarHourlyData.objects.bulk_create(objects)

        self.stdout.write(f"Inserted {len(objects)} records successfully")
