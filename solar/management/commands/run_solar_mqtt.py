import os
import json
import logging
import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from solar.models import SolarHourlyData, WashRecord, DeviceLocation

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Runs MQTT listener for Solar devices"

    def handle(self, *args, **options):
        # ================= MQTT CONFIG =================
        MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt.ezrun.in")
        MQTT_PORT   = int(os.getenv("MQTT_PORT", 1883))
        MQTT_USER   = os.getenv("MQTT_USER", "nk")
        MQTT_PASS   = os.getenv("MQTT_PASS", "9898434411")

        TOPIC_SUBSCRIPTION = "solar/+/data/#"

        # ================= MQTT CALLBACKS =================
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.stdout.write(self.style.SUCCESS("✓ Connected to MQTT Broker"))
                client.subscribe(TOPIC_SUBSCRIPTION)
            else:
                self.stdout.write(self.style.ERROR(f"✗ MQTT connect failed, rc={rc}"))

        def on_message(client, userdata, msg):
            try:
                topic = msg.topic
                payload = msg.payload.decode("utf-8")
                data = json.loads(payload)

                device_id = data.get("device_id")
                voltage   = float(data.get("voltage", 0))
                current   = float(data.get("current", 0))
                power     = float(data.get("power", 0))

                if not device_id:
                    logger.warning("Missing device_id in payload")
                    return

                # ================= GET DEVICE LOCATION =================
                location = DeviceLocation.objects.filter(
                    device_id=device_id
                ).first()

                lat = location.lat if location else None
                lon = location.lon if location else None

                # ================= SAVE DATA =================
                if topic.endswith("/hourly"):
                    SolarHourlyData.objects.create(
                        device_id=device_id,
                        voltage=voltage,
                        current=current,
                        power=power,
                        energy=power,  # avg W over hour (you can refine later)
                        lat=lat,
                        lon=lon,
                    )
                    print(f"✓ Hourly data saved for {device_id} ({power} W)")

                elif topic.endswith("/before_wash"):
                    WashRecord.objects.create(
                        device_id=device_id,
                        wash_type="BEFORE",
                        voltage=voltage,
                        current=current,
                        power=power,
                    )
                    print(f"✓ BEFORE wash saved for {device_id}")

                elif topic.endswith("/after_wash"):
                    WashRecord.objects.create(
                        device_id=device_id,
                        wash_type="AFTER",
                        voltage=voltage,
                        current=current,
                        power=power,
                    )
                    print(f"✓ AFTER wash saved for {device_id}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {msg.payload}")
            except Exception as e:
                logger.exception(f"Error processing MQTT message: {e}")

        # ================= MQTT CLIENT =================
        client = mqtt.Client()
        client.username_pw_set(MQTT_USER, MQTT_PASS)
        client.on_connect = on_connect
        client.on_message = on_message

        self.stdout.write("Connecting to MQTT broker...")

        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            client.loop_forever()
        except KeyboardInterrupt:
            self.stdout.write("MQTT listener stopped.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"MQTT connection error: {e}"))
