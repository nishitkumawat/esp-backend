import os
import json
import logging
import requests
import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from django.conf import settings
from solar.models import SolarHourlyData, WashRecord, DeviceLocation

logger = logging.getLogger(__name__)

# Cache for device locations (in-memory for this process)
device_location_cache = {}

def get_location_from_ip(ip_address):
    """
    Fetch geolocation (lat, lon, city, state, country) from IP address.
    Uses ip-api.com (free, no key required, 45 req/min limit)
    """
    try:
        # Skip private/local IPs
        if ip_address.startswith(('127.', '192.168.', '10.', '172.')):
            logger.warning(f"Private IP detected: {ip_address}, using default location")
            return None
            
        url = f"http://ip-api.com/json/{ip_address}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'city': data.get('city', 'Unknown'),
                    'state': data.get('regionName', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'zip': data.get('zip', ''),
                }
        logger.error(f"Failed to fetch location for IP {ip_address}")
        return None
    except Exception as e:
        logger.error(f"Error fetching location for IP {ip_address}: {e}")
        return None

def get_or_create_device_location(device_id, client_ip=None):
    """
    Get cached location for device, or fetch from IP if not cached.
    """
    # Check cache first
    if device_id in device_location_cache:
        return device_location_cache[device_id]
    
    # Try to get from database
    try:
        from solar.models import DeviceLocation
        location = DeviceLocation.objects.filter(device_id=device_id).first()
        if location:
            device_location_cache[device_id] = {
                'lat': location.lat,
                'lon': location.lon,
                'city': location.city,
                'state': location.state,
            }
            return device_location_cache[device_id]
    except Exception as e:
        logger.error(f"Error fetching device location from DB: {e}")
    
    # If we have client IP, fetch location
    if client_ip:
        location_data = get_location_from_ip(client_ip)
        if location_data:
            try:
                # Save to database
                DeviceLocation.objects.update_or_create(
                    device_id=device_id,
                    defaults={
                        'lat': location_data['lat'],
                        'lon': location_data['lon'],
                        'city': location_data['city'],
                        'state': location_data['state'],
                        'country': location_data.get('country', ''),
                        'zip_code': location_data.get('zip', ''),
                    }
                )
                # Cache it
                device_location_cache[device_id] = {
                    'lat': location_data['lat'],
                    'lon': location_data['lon'],
                    'city': location_data['city'],
                    'state': location_data['state'],
                }
                logger.info(f"Saved new location for {device_id}: {location_data['city']}, {location_data['state']}")
                return device_location_cache[device_id]
            except Exception as e:
                logger.error(f"Error saving device location: {e}")
    
    return None

class Command(BaseCommand):
    help = 'Runs the MQTT listener for Solar data with automatic geolocation'

    def handle(self, *args, **options):
        # MQTT Config
        MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt.ezrun.in")
        MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
        MQTT_USER = os.getenv("MQTT_USER", "nk")
        MQTT_PASS = os.getenv("MQTT_PASS", "9898434411")
        
        # Topics to subscribe
        # solar/+/data/hourly
        # solar/+/data/before_wash
        # solar/+/data/after_wash
        TOPIC_SUBSCRIPTION = "solar/+/data/#"

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.stdout.write(self.style.SUCCESS('Connected to MQTT Broker!'))
                client.subscribe(TOPIC_SUBSCRIPTION)
            else:
                self.stdout.write(self.style.ERROR(f'Failed to connect, return code {rc}'))

        def on_message(client, userdata, msg):
            try:
                topic = msg.topic
                payload_str = msg.payload.decode('utf-8')
                data = json.loads(payload_str)
                
                # Payload: {"device_id":"...", "voltage":..., "current":..., "power":...}
                
                device_id = data.get('device_id')
                voltage = float(data.get('voltage', 0))
                current = float(data.get('current', 0))
                power = float(data.get('power', 0))
                
                # Check if ESP sent lat/lon manually
                lat = data.get('lat')
                lon = data.get('lon')
                
                if not device_id:
                    return

                # Get location (from cache, DB, or IP lookup)
                # Note: MQTT doesn't expose client IP directly in paho-mqtt
                # We'll rely on the database cache or manual lat/lon from ESP
                location_data = get_or_create_device_location(device_id)
                
                if not lat and location_data:
                    lat = location_data.get('lat')
                    lon = location_data.get('lon')

                if "hourly" in topic:
                    SolarHourlyData.objects.create(
                        device_id=device_id,
                        voltage=voltage,
                        current=current,
                        power=power,
                        energy=power, # Assuming power is avg power over hour
                        lat=lat,
                        lon=lon
                    )
                    logger.info(f"Saved Hourly Data for {device_id}")
                    print(f"✓ Saved Hourly Data for {device_id} (P={power}W)")
                    
                elif "before_wash" in topic:
                    WashRecord.objects.create(
                        device_id=device_id,
                        wash_type='BEFORE',
                        voltage=voltage,
                        current=current,
                        power=power
                    )
                    logger.info(f"Saved BEFORE Wash Data for {device_id}")
                    print(f"✓ Saved BEFORE Wash for {device_id}")

                elif "after_wash" in topic:
                    WashRecord.objects.create(
                        device_id=device_id,
                        wash_type='AFTER',
                        voltage=voltage,
                        current=current,
                        power=power
                    )
                    logger.info(f"Saved AFTER Wash Data for {device_id}")
                    print(f"✓ Saved AFTER Wash for {device_id}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {msg.payload}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                print(f"✗ Error: {e}")

        client = mqtt.Client()
        client.username_pw_set(MQTT_USER, MQTT_PASS)
        client.on_connect = on_connect
        client.on_message = on_message

        self.stdout.write("Connecting to MQTT...")
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            client.loop_forever()
        except KeyboardInterrupt:
            self.stdout.write("Stopped.")
        except Exception as e:
             self.stdout.write(self.style.ERROR(f"Connection Error: {e}"))

