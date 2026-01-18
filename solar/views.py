from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import calendar
import json
import requests

from .models import SolarHourlyData, WashRecord, DeviceLocation


def json_response(status: bool, message: str, status_code: int = 200, **extra):
    payload = {"status": status, "message": message}
    if extra:
        payload.update(extra)
    return JsonResponse(payload, status=status_code)

@csrf_exempt
def get_latest_solar_data(request):
    """
    GET /api/solar/latest?device_id=...
    Always returns a response.
    If no data exists, returns zeros with current timestamp.
    """
    device_id = request.GET.get('device_id')

    if not device_id:
        return json_response(False, "Missing device_id", status_code=400)

    latest = (
        SolarHourlyData.objects
        .filter(device_id=device_id)
        .order_by('-timestamp')
        .first()
    )

    if latest:
        data = {
            "timestamp": latest.timestamp.isoformat(),
            "power": latest.power,
            "voltage": latest.voltage,
            "current": latest.current,
            "energy": latest.energy
        }
    else:
        # No data → return zero values
        now = timezone.now()
        data = {
            "timestamp": now.isoformat(),
            "power": 0,
            "voltage": 0,
            "current": 0,
            "energy": 0
        }

    return json_response(True, "Success", data=data)

@csrf_exempt
def get_solar_stats(request):
    device_id = request.GET.get('device_id')
    period = request.GET.get('period')  # day | month | year

    if not device_id or not period:
        return json_response(False, "device_id and period are required", status_code=400)

    data_points = []
    total_yield = 0.0
    avg_power = 0.0

    # Fetch Location, Price and Capacity
    location_obj = DeviceLocation.objects.filter(device_id=device_id).first()
    price_per_unit = 5.0
    if location_obj:
        price_per_unit = location_obj.price

    # ===================== DAY =====================
    if period == "day":
        date_str = request.GET.get("date")  # YYYY-MM-DD
        if not date_str:
            # Default to today if not provided
            date_str = timezone.now().strftime("%Y-%m-%d")

        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        start_time = timezone.make_aware(
            datetime.combine(selected_date, datetime.min.time())
        )
        end_time = timezone.make_aware(
            datetime.combine(selected_date, datetime.max.time())
        )

        qs = SolarHourlyData.objects.filter(
            device_id=device_id,
            timestamp__range=(start_time, end_time)
        ).order_by("timestamp")

        powers = []
        for item in qs:
            data_points.append({
                "time": item.timestamp.strftime("%H:%M"),
                "power": item.power
            })
            powers.append(item.power)
        
        if powers:
            # Assuming hourly data points, sum of power is Wh
            total_yield = sum(powers)
            avg_power = sum(powers) / len(powers)

    # ===================== MONTH =====================
    elif period == "month":
        month_str = request.GET.get("month")  # YYYY-MM
        if not month_str:
            month_str = timezone.now().strftime("%Y-%m")

        year, month = map(int, month_str.split("-"))

        start_time = timezone.make_aware(datetime(year, month, 1))
        last_day = calendar.monthrange(year, month)[1]
        end_time = timezone.make_aware(datetime(year, month, last_day, 23, 59, 59))

        qs = (
            SolarHourlyData.objects
            .filter(device_id=device_id, timestamp__range=(start_time, end_time))
            .annotate(day=TruncDay("timestamp"))
            .values("day")
            .annotate(avg_p=Avg("power"))
            .order_by("day")
        )

        total_p = 0
        count = 0
        for item in qs:
            data_points.append({
                "time": item["day"].strftime("%d-%b"),
                "power": round(item["avg_p"], 2)
            })
            total_p += item["avg_p"]
            count += 1
        
        if count > 0:
            # For month, yield is roughly sum of hourly power, but we have daily averages here.
            # It's better to fetch all hourly for yield or use avg * 24 * days.
            # Let's get actual sum from hourly data for accuracy.
            total_yield = SolarHourlyData.objects.filter(
                device_id=device_id, 
                timestamp__range=(start_time, end_time)
            ).aggregate(models.Sum('power'))['power__sum'] or 0.0
            avg_power = total_p / count

    # ===================== YEAR =====================
    elif period == "year":
        year_str = request.GET.get("year")  # YYYY
        if not year_str:
            year_str = timezone.now().strftime("%Y")

        year = int(year_str)

        start_time = timezone.make_aware(datetime(year, 1, 1))
        end_time = timezone.make_aware(datetime(year, 12, 31, 23, 59, 59))

        qs = (
            SolarHourlyData.objects
            .filter(device_id=device_id, timestamp__range=(start_time, end_time))
            .annotate(month=TruncMonth("timestamp"))
            .values("month")
            .annotate(avg_p=Avg("power"))
            .order_by("month")
        )

        total_p = 0
        count = 0
        for item in qs:
            data_points.append({
                "time": item["month"].strftime("%b"),
                "power": round(item["avg_p"], 2)
            })
            total_p += item["avg_p"]
            count += 1
            
        if count > 0:
            total_yield = SolarHourlyData.objects.filter(
                device_id=device_id, 
                timestamp__range=(start_time, end_time)
            ).aggregate(models.Sum('power'))['power__sum'] or 0.0
            avg_power = total_p / count

    money_saved = (total_yield / 1000.0) * price_per_unit

    wash_records = WashRecord.objects.filter(device_id=device_id).order_by('-timestamp')
    
    wash_data = {'before': None, 'after': None}
    
    for i, record in enumerate(wash_records):
        if record.wash_type == 'AFTER':
            if i + 1 < len(wash_records):
                prev_record = wash_records[i+1]
                if prev_record.wash_type == 'BEFORE':
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
                    break
            
    location_data = {"city": "Unknown", "state": "Unknown", "temperature": None, "lat": None, "lon": None, "price": price_per_unit, "capacity": 5.0}
    if location_obj:
        location_data["city"] = location_obj.city
        location_data["state"] = location_obj.state
        location_data["lat"] = location_obj.lat
        location_data["lon"] = location_obj.lon
        location_data["price"] = location_obj.price
        location_data["capacity"] = location_obj.capacity
        
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
    
    current_power = 0.0
    latest_reading = SolarHourlyData.objects.filter(device_id=device_id).order_by('-timestamp').first()
    if latest_reading:
        current_power = latest_reading.power

    return json_response(
        True, "Stats fetched", 
        data=data_points, 
        wash=wash_data, 
        location=location_data, 
        current_power=current_power,
        period_yield=round(total_yield, 2),
        avg_power=round(avg_power, 2),
        money_saved=round(money_saved, 2)
    )

from .models import SolarAlert

@csrf_exempt
def get_solar_alerts(request):
    device_id = request.GET.get('device_id')
    if not device_id:
        return json_response(False, "device_id is required", status_code=400)
    
    alerts = SolarAlert.objects.filter(device_id=device_id)[:50]
    data = []
    for a in alerts:
        data.append({
            "id": a.id,
            "title": a.title,
            "message": a.message,
            "alert_type": a.alert_type,
            "timestamp": a.timestamp.isoformat()
        })
    
    return json_response(True, "Alerts fetched", alerts=data)

def create_solar_alert(device_id, title, message, alert_type='info'):
    SolarAlert.objects.create(
        device_id=device_id,
        title=title,
        message=message,
        alert_type=alert_type
    )

@csrf_exempt
@require_http_methods(["POST"])
def record_wash_alert(request):
    """
    Called when a wash is triggered to record an alert.
    """
    try:
        data = json.loads(request.body)
        device_id = data.get("device_id")
        if not device_id:
            return json_response(False, "device_id is required", status_code=400)
        
        create_solar_alert(
            device_id=device_id,
            title="Solar Cleaning Started",
            message=f"A cleaning cycle has been triggered for device {device_id}.",
            alert_type="success"
        )
        return json_response(True, "Alert recorded")
    except Exception as e:
        return json_response(False, str(e), status_code=500)

# @csrf_exempt
# def ping_location(request):
#     """
#     ESP pings after Wi-Fi setup or boot.

#     Priority:
#     1) GPS lat/lon from Wi-Fi setup (phone browser)
#     2) IP-based fallback (low accuracy)
#     """

#     device_id = request.GET.get("device_id")
#     if not device_id:
#         return json_response(False, "Missing device_id", status_code=400)

#     # =====================================================
#     # 1️⃣ GPS-BASED LOCATION (BEST & ACCURATE)
#     # =====================================================
#     lat = request.GET.get("lat")
#     lon = request.GET.get("lon")

#     if lat and lon:
#         try:
#             # 🌍 Reverse geocoding (FREE)
#             geo_url = (
#                 "https://geocoding-api.open-meteo.com/v1/reverse"
#                 f"?latitude={lat}&longitude={lon}&language=en"
#             )
#             geo_res = requests.get(geo_url, timeout=5)
#             geo_data = geo_res.json()

#             city = state = country = zip_code = "Unknown"

#             if geo_data.get("results"):
#                 r = geo_data["results"][0]
#                 city = r.get("city") or r.get("town") or r.get("village") or "Unknown"
#                 state = r.get("admin1") or "Unknown"
#                 country = r.get("country") or ""
#                 zip_code = r.get("postcode") or ""

#             DeviceLocation.objects.update_or_create(
#                 device_id=device_id,
#                 defaults={
#                     "lat": float(lat),
#                     "lon": float(lon),
#                     "city": city,
#                     "state": state,
#                     "country": country,
#                     "zip_code": zip_code,
#                 }
#             )

#             return json_response(
#                 True,
#                 "Location saved from GPS",
#                 lat=lat,
#                 lon=lon,
#                 city=city,
#                 state=state,
#                 country=country,
#                 zip_code=zip_code,
#                 source="gps",
#             )

#         except Exception as e:
#             return json_response(
#                 False,
#                 "GPS reverse geocoding failed",
#                 error=str(e),
#                 status_code=500,
#             )

#     # =====================================================
#     # 2️⃣ IP-BASED FALLBACK (LIMITED ACCURACY)
#     # =====================================================
#     ip = get_client_ip(request)

#     if not ip or ip.startswith(("127.", "192.168.", "10.", "172.")):
#         return json_response(
#             True,
#             "Ping received (no usable location)",
#             source="none",
#             ip=ip,
#         )

#     try:
#         ip_res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
#         data = ip_res.json()

#         if data.get("status") != "success":
#             return json_response(False, "IP location failed", ip=ip)

#         DeviceLocation.objects.update_or_create(
#             device_id=device_id,
#             defaults={
#                 "lat": data.get("lat"),
#                 "lon": data.get("lon"),
#                 "city": data.get("city", "Unknown"),
#                 "state": data.get("regionName", "Unknown"),
#                 "country": data.get("country", ""),
#                 "zip_code": data.get("zip", ""),
#             }
#         )

#         return json_response(
#             True,
#             "Location saved from IP",
#             city=data.get("city"),
#             state=data.get("regionName"),
#             country=data.get("country"),
#             zip_code=data.get("zip"),
#             source="ip",
#         )

#     except Exception as e:
#         return json_response(
#             False,
#             "IP location error",
#             error=str(e),
#             status_code=500,
#         )


@csrf_exempt
def record_wash(request):
    # This might not be needed if we rely solely on MQTT, but good to have API backup
    pass

# def get_client_ip(request):
#     """
#     Get real client IP even behind nginx / proxy
#     """
#     x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
#     if x_forwarded_for:
#         # First IP is the real client
#         return x_forwarded_for.split(",")[0].strip()
#     return request.META.get("REMOTE_ADDR")


# def complete_setup(request):
#     """
#     Renders the device setup completion page
#     """
#     device_id = request.GET.get('device_id')
#     if not device_id:
#         return HttpResponse("Device ID is required", status=400)
        
#     html_content = """
#     <!DOCTYPE html>
#     <html>
#     <head>
#       <meta name="viewport" content="width=device-width, initial-scale=1">
#       <title>Setup Complete</title>
#       <style>
#         body { font-family: Arial; text-align: center; padding: 40px; }
#         h2 { color: #1e90ff; }
#       </style>
#     </head>
#     <body>
#       <h2>🎉 Setup Almost Complete</h2>
#       <p>We're setting up weather & solar analytics.</p>
#       <p>Device ID: %s</p>
#       <script>
#       const deviceId = "%s";
#       if (navigator.geolocation) {
#         navigator.geolocation.getCurrentPosition(
#           pos => {
#             fetch("/api/device/location", {
#               method: "POST",
#               headers: { "Content-Type": "application/json" },
#               body: JSON.stringify({
#                 device_id: deviceId,
#                 lat: pos.coords.latitude,
#                 lon: pos.coords.longitude
#               })
#             }).then(() => {
#               document.body.innerHTML =
#                 "<h2>✅ Setup Complete</h2><p>You can now use the app.</p>";
#             }).catch(err => {
#               document.body.innerHTML =
#                 "<h2>⚠️ Error</h2><p>Failed to save location. Please try again.</p>";
#             });
#           },
#           err => {
#             document.body.innerHTML =
#               "<h2>⚠️ Location Required</h2><p>Please allow location for accurate data.</p>";
#           }
#         );
#       } else {
#         document.body.innerHTML =
#           "<h2>⚠️ Location Not Supported</h2><p>Your browser doesn't support geolocation.</p>";
#       }
#       </script>
#     </body>
#     </html>
#     """ % (device_id, device_id)
    
#     return HttpResponse(html_content)

@csrf_exempt
@require_http_methods(["POST"])
def save_device_location(request):
    try:
        data = json.loads(request.body)

        device_id = data.get("device_id")
        state = data.get("state")
        city = data.get("city")

        if not device_id:
            return JsonResponse(
                {"status": False, "message": "device_id required"},
                status=400
            )

        if not state or not city:
            return JsonResponse(
                {"status": False, "message": "state and city required"},
                status=400
            )

        # OPTIONAL: Convert city -> lat/lon (FREE)
        lat, lon = geocode_city(city, state)

        DeviceLocation.objects.update_or_create(
            device_id=device_id,
            defaults={
                "state": state,
                "city": city,
                "lat": lat,
                "lon": lon,
               #"source": "manual",
                "last_updated": timezone.now()
            }
        )

        return JsonResponse({
            "status": True,
            "message": "Location saved",
            "device_id": device_id,
            "state": state,
            "city": city,
            "lat": lat,
            "lon": lon
        })

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": False, "message": "Invalid JSON"},
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {"status": False, "message": str(e)},
            status=500
        )

import requests

def city_from_ip(ip):
    r = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
    data = r.json()

    if data.get("status") != "success":
        return None, None, None, None

    return (
        data.get("lat"),
        data.get("lon"),
        data.get("city"),
        data.get("country")
    )

def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

def geocode_city(city, state):
    try:
        url = (
            "https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city}&count=1&language=en"
        )
        r = requests.get(url, timeout=4)
        data = r.json()

        if data.get("results"):
            res = data["results"][0]
            return res.get("latitude"), res.get("longitude")

    except Exception as e:
        print("Geocoding failed:", e)

    return None, None
