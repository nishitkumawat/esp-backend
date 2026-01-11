import os
import json
import logging
import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from django.conf import settings
from solar.models import SolarHourlyData, WashRecord

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Runs the MQTT listener for Solar data'

    def handle(self, *args, **options):
        # MQTT Config
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
                lat = data.get('lat')
                lon = data.get('lon')
                
                if not device_id:
                    return

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
                    print(f"Saved Hourly Data for {device_id}")
                    
                elif "before_wash" in topic:
                    WashRecord.objects.create(
                        device_id=device_id,
                        wash_type='BEFORE',
                        voltage=voltage,
                        current=current,
                        power=power
                    )
                    logger.info(f"Saved BEFORE Wash Data for {device_id}")
                    print(f"Saved BEFORE Wash Data for {device_id}")

                elif "after_wash" in topic:
                    WashRecord.objects.create(
                        device_id=device_id,
                        wash_type='AFTER',
                        voltage=voltage,
                        current=current,
                        power=power
                    )
                    logger.info(f"Saved AFTER Wash Data for {device_id}")
                    print(f"Saved AFTER Wash Data for {device_id}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {msg.payload}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                print(f"Error: {e}")

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
