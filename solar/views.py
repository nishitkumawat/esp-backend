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
        # Detailed aggregation in Django ORM can be complex across DBs (sqlite vs mysql)
        # For simplicity/speed, we fetch hourly and aggregate in python or use basic filtering
        # Ideally, use TruncDay.
        from django.db.models.functions import TruncDay
        
        qs = SolarHourlyData.objects.filter(
            device_id=device_id,
            timestamp__gte=start_time
        ).annotate(day=TruncDay('timestamp')).values('day').annotate(avg_power=Avg('power')).order_by('day')

        for item in qs:
            data_points.append({
                "time": item['day'].strftime("%d-%b"), # 12-Jan
                "power": round(item['avg_power'], 2)
            })

    # Fetch last wash details
    last_after = WashRecord.objects.filter(device_id=device_id, wash_type='AFTER').first()
    last_before = WashRecord.objects.filter(device_id=device_id, wash_type='BEFORE').first()
    
    wash_data = {}
    if last_after:
        wash_data['after'] = {
            "voltage": last_after.voltage,
            "current": last_after.current,
            "power": last_after.power,
            "timestamp": last_after.timestamp.isoformat()
        }
    else:
        wash_data['after'] = None
        
    if last_before:
        # We might want the 'before' that corresponds to the 'after'. 
        # Usually checking if before.timestamp < after.timestamp and not too far apart.
        # For simple UI, just showing latest available.
        wash_data['before'] = {
            "voltage": last_before.voltage,
            "current": last_before.current,
            "power": last_before.power,
            "timestamp": last_before.timestamp.isoformat()
        }
    else:
        wash_data['before'] = None

    return json_response(True, "Stats fetched", data=data_points, wash=wash_data)

@csrf_exempt
def record_wash(request):
    # This might not be needed if we rely solely on MQTT, but good to have API backup
    pass
