from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
import json
from .models import SolarHourlyData, WashRecord

def json_response(status: bool, message: str, status_code: int = 200, **extra):
    payload = {"status": status, "message": message}
    if extra:
        payload.update(extra)
    return JsonResponse(payload, status=status_code)

@csrf_exempt
def get_solar_stats(request):
    """
    GET /api/solar/stats?device_id=...&period=day|month
    """
    device_id = request.GET.get('device_id')
    period = request.GET.get('period', 'day') # day, month
    
    if not device_id:
        return json_response(False, "Missing device_id", status_code=400)

    now = timezone.now()
    
    data_points = []
    
    if period == 'day':
        # Last 24 hours hourly data
        start_time = now - timedelta(hours=24)
        qs = SolarHourlyData.objects.filter(
            device_id=device_id, 
            timestamp__gte=start_time
        ).order_by('timestamp')
        
        for item in qs:
            data_points.append({
                "time": item.timestamp.strftime("%H:%M"),
                "power": item.power
            })
            
    elif period == 'month':
        # Last 30 days, daily average
        start_time = now - timedelta(days=30)
        from django.db.models.functions import TruncDay
        
        qs = SolarHourlyData.objects.filter(
            device_id=device_id,
            timestamp__gte=start_time
        ).annotate(date=TruncDay('timestamp')).values('date').annotate(avg_power=Avg('power')).order_by('date')

        for item in qs:
            data_points.append({
                "time": item['date'].strftime("%d-%b"), # 12-Jan
                "power": round(item['avg_power'], 2)
            })

    elif period == 'year':
        # Last 12 months, monthly average
        start_time = now - timedelta(days=365)
        from django.db.models.functions import TruncMonth
        
        qs = SolarHourlyData.objects.filter(
            device_id=device_id,
            timestamp__gte=start_time
        ).annotate(month=TruncMonth('timestamp')).values('month').annotate(avg_power=Avg('power')).order_by('month')

        for item in qs:
            data_points.append({
                "time": item['month'].strftime("%b-%y"), # Jan-24
                "power": round(item['avg_power'], 2)
            })

    # Fetch wash details with REVERSE logic (Find AFTER, then preceding BEFORE)
    # Fetch all records DESCENDING (latest first)
    wash_records = WashRecord.objects.filter(device_id=device_id).order_by('-timestamp')
    
    wash_data = {'before': None, 'after': None}
    
    # Iterate to find the first 'AFTER' wash
    for i, record in enumerate(wash_records):
        if record.wash_type == 'AFTER':
            # Look ahead (which is future in list index, but past in time) for immediately preceding record
            if i + 1 < len(wash_records):
                prev_record = wash_records[i+1] # The one before this 'AFTER'
                if prev_record.wash_type == 'BEFORE':
                    # Found our pair
                    wash_data['after'] = {
                        "voltage": record.voltage,
                        "current": record.current,
                        "power": record.power,
                        "timestamp": record.timestamp.isoformat()
                    }
                    wash_data['before'] = {
                        "voltage": prev_record.voltage,
                        "current": prev_record.current,
                        "power": prev_record.power,
                        "timestamp": prev_record.timestamp.isoformat()
                    }
                    break # Stop after finding the latest valid pair
            
            # If we found an AFTER but no immediately preceding BEFORE, we ignore it 
            # (or we could show it as orphaned, but user prompt implies strictness "enter just after its before")
            
    # Fetch Location
    location_data = {"city": "Unknown", "state": "Unknown"}
    last_data = SolarHourlyData.objects.filter(device_id=device_id).order_by('-timestamp').first()
    
    if last_data and last_data.lat and last_data.lon:
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="machmate_solar_app")
            # timeout is important so we don't block too long
            location = geolocator.reverse((last_data.lat, last_data.lon), language='en', timeout=2)
            
            if location:
                address = location.raw.get('address', {})
                city = address.get('city') or address.get('town') or address.get('village') or ""
                state = address.get('state') or ""
                location_data = {"city": city, "state": state}
                
        except Exception as e:
            print(f"Geocoding error: {e}")

    return json_response(True, "Stats fetched", data=data_points, wash=wash_data, location=location_data)

@csrf_exempt
def record_wash(request):
    # This might not be needed if we rely solely on MQTT, but good to have API backup
    pass
