import os, json, logging, threading, requests
import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from solar.models import SolarHourlyData, WashRecord, DeviceLocation, WeatherLog

logger = logging.getLogger(__name__)


def check_rain(lat, lon, threshold, device_id=None):
    """Query Open-Meteo for precipitation. Returns True=skip wash. Fail-safe: False on error."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly=precipitation&past_days=1&forecast_days=1"
        )
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            logger.warning(f"[Rain] API request failed with status {r.status_code}")
            return False
            
        data = r.json()
        precipitation = data.get("hourly", {}).get("precipitation", [])
        
        # Last 24 hrs only
        last_24h = precipitation[:24]
        
        # Find max rain event
        max_rain = max((float(v) for v in last_24h if v is not None), default=0)
        logger.info(f"[Rain] max={max_rain}mm threshold={threshold}mm")
        skip = max_rain >= threshold

        # Save every weather/rain API response to WeatherLog
        try:
            WeatherLog.objects.create(
                device_id=device_id or "unknown",
                lat=lat,
                lon=lon,
                temperature=None,          # precipitation check — no temp
                weather_code=None,         # not returned in this endpoint
                max_rain=max_rain,
                skip_wash=skip,
                raw_response=data,
            )
        except Exception as log_err:
            logger.warning(f"[Rain] WeatherLog save failed: {log_err}")

        return skip
    except Exception as e:
        logger.warning(f"[Rain] API error (fail-safe wash allowed): {e}")
        return False


class Command(BaseCommand):
    help = "MQTT listener: Solar data + Rain weather check"

    def handle(self, *args, **options):
        BROKER = os.getenv("MQTT_BROKER", "mqtt.ezrun.in")
        PORT   = int(os.getenv("MQTT_PORT", 1883))
        USER   = os.getenv("MQTT_USER", "nk")
        PASS   = os.getenv("MQTT_PASS", "9898434411")

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.stdout.write(self.style.SUCCESS("✓ MQTT Connected"))
                client.subscribe("solar/+/data/#")
                client.subscribe("solar/+/weather/check")
            else:
                self.stdout.write(self.style.ERROR(f"✗ MQTT rc={rc}"))

        def weather_thread(client, device_id, payload_str):
            def _run():
                try:
                    d = json.loads(payload_str)
                    lat = float(d.get("lat", 0))
                    lon = float(d.get("lon", 0))
                    thr = float(d.get("threshold", 3))
                    skip = check_rain(lat, lon, thr, device_id=device_id) if (lat or lon) else False
                    resp = json.dumps({"skip_wash": skip})
                    client.publish(f"solar/{device_id}/weather/response", resp, qos=1)
                    self.stdout.write(f"{'SKIP' if skip else 'WASH'} {device_id} lat={lat} lon={lon}")
                except Exception as e:
                    logger.error(f"[Weather] {device_id}: {e}")
                    try:
                        client.publish(f"solar/{device_id}/weather/response",
                                       json.dumps({"skip_wash": False}), qos=1)
                    except Exception:
                        pass
            threading.Thread(target=_run, daemon=True).start()

        def on_message(client, userdata, msg):
            try:
                topic = msg.topic
                payload = msg.payload.decode("utf-8")

                if "/weather/check" in topic:
                    parts = topic.split("/")
                    if len(parts) >= 3:
                        weather_thread(client, parts[1], payload)
                    return

                data = json.loads(payload)
                device_id = data.get("device_id")
                if not device_id:
                    return
                voltage = float(data.get("voltage", 0))
                current = float(data.get("current", 0))
                power   = float(data.get("power", 0))

                if topic.endswith("/hourly"):
                    SolarHourlyData.objects.create(
                        device_id=device_id, voltage=voltage,
                        current=current, power=power, energy=power)
                    print(f"✓ Hourly {device_id} ({power}W)")
                elif topic.endswith("/before_wash"):
                    WashRecord.objects.create(device_id=device_id, wash_type="BEFORE",
                        voltage=voltage, current=current, power=power)
                elif topic.endswith("/after_wash"):
                    WashRecord.objects.create(device_id=device_id, wash_type="AFTER",
                        voltage=voltage, current=current, power=power)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {msg.payload}")
            except Exception as e:
                logger.exception(f"MQTT error: {e}")

        client = mqtt.Client()
        client.username_pw_set(USER, PASS)
        client.on_connect = on_connect
        client.on_message = on_message
        try:
            client.connect(BROKER, PORT, 60)
            client.loop_forever()
        except KeyboardInterrupt:
            self.stdout.write("MQTT listener stopped.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
