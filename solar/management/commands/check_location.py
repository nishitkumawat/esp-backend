from django.core.management.base import BaseCommand
from solar.models import SolarHourlyData
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

class Command(BaseCommand):
    help = 'Test Geocoding'

    def handle(self, *args, **options):
        device_id = "1CSNISHITKUMAWAT"
        total = SolarHourlyData.objects.filter(device_id=device_id).count()
        with_loc = SolarHourlyData.objects.filter(device_id=device_id, lat__isnull=False).count()
        
        self.stdout.write(f"Total Records: {total}")
        self.stdout.write(f"Records with Location: {with_loc}")

        last_data = SolarHourlyData.objects.filter(device_id=device_id).order_by('-timestamp').first()
        
        if not last_data:
            self.stdout.write(self.style.ERROR("No data found"))
            return

        self.stdout.write(f"Latest Data: Lat={last_data.lat}, Lon={last_data.lon}")
        
        if not last_data.lat or not last_data.lon:
             self.stdout.write(self.style.ERROR("Lat/Lon missing"))
             return

        try:
            geolocator = Nominatim(user_agent="machmate_test_debug_v1")
            location = geolocator.reverse((last_data.lat, last_data.lon), language='en', timeout=10)
            
            if location:
                self.stdout.write(f"FULL RAW: {location.raw}")
                address = location.raw.get('address', {})
                city = address.get('city') or address.get('town') or address.get('village') or ""
                state = address.get('state') or ""
                self.stdout.write(self.style.SUCCESS(f"RESOLVED -> City: '{city}', State: '{state}'"))
            else:
                self.stdout.write(self.style.WARNING("No location found (Geolocator returned None)"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"GEOCODING EXCEPTION: {e}"))
            import traceback
            traceback.print_exc()
