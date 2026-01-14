from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
import json
import requests
from .models import SolarHourlyData, WashRecord, DeviceLocation

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
            
    # Fetch Location and Temperature
    location_data = {"city": "Unknown", "state": "Unknown", "temperature": None, "lat": None, "lon": None}
    
    # Get location from DeviceLocation table
    location_obj = DeviceLocation.objects.filter(device_id=device_id).first()
    
    if location_obj:
        location_data["city"] = location_obj.city
        location_data["state"] = location_obj.state
        location_data["lat"] = location_obj.lat
        location_data["lon"] = location_obj.lon
        
        # Fetch temperature and weather_code from weather API
        try:
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={location_obj.lat}&longitude={location_obj.lon}&current=temperature_2m,weather_code"
            weather_response = requests.get(weather_url, timeout=3)
            
            if weather_response.status_code == 200:
                weather_data = weather_response.json()
                if 'current' in weather_data:
                    if 'temperature_2m' in weather_data['current']:
                        location_data["temperature"] = weather_data['current']['temperature_2m']
                    if 'weather_code' in weather_data['current']:
                        location_data["weather_code"] = weather_data['current']['weather_code']
                    
        except Exception as e:
            print(f"Weather API error: {e}")
    
    # Fetch current power (most recent reading)
    current_power = 0.0
    latest_reading = SolarHourlyData.objects.filter(device_id=device_id).order_by('-timestamp').first()
    if latest_reading:
        current_power = latest_reading.power

    return json_response(True, "Stats fetched", data=data_points, wash=wash_data, location=location_data, current_power=current_power)

@csrf_exempt
def ping_location(request):
    """
    ESP pings this on startup: /api/solar/ping?device_id=...
    Backend fetches location from IP and updates DeviceLocation.
    """
    device_id = request.GET.get('device_id')
    if not device_id:
        return json_response(False, "Missing device_id", status_code=400)
    
    # Get public IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # For local testing, handle loopback
    if ip == '127.0.0.1' or ip == '::1' or ip.startswith('192.168.'):
        # We can't geolocate local IPs, so we'll just acknowledge the ping
        return json_response(True, "Ping received (Internal/Local IP)", ip=ip)

    try:
        # Use ip-api.com (free for non-commercial use, 45 requests/min)
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                DeviceLocation.objects.update_or_create(
                    device_id=device_id,
                    defaults={
                        'lat': data.get('lat'),
                        'lon': data.get('lon'),
                        'city': data.get('city', 'Unknown'),
                        'state': data.get('regionName', 'Unknown'),
                        'country': data.get('country', ''),
                        'zip_code': data.get('zip', ''),
                    }
                )
                return json_response(True, "Location updated", city=data.get('city'), ip=ip)
            else:
                return json_response(False, f"IP Geolocation failed: {data.get('message')}", ip=ip)
    except Exception as e:
        print(f"IP-based Geolocation error: {e}")
        return json_response(False, f"Error updating location: {str(e)}", status_code=500)
        
    return json_response(False, "Failed to update location", status_code=500)

@csrf_exempt
def record_wash(request):
    # This might not be needed if we rely solely on MQTT, but good to have API backup
    pass
