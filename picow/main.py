# main.py (MicroPython para Pico W)
import time
import network
import ujson
from umqtt.simple import MQTTClient
import secrets

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)

# Espera la conexión (con timeout)
timeout = 15
start = time.time()
while not wlan.isconnected() and time.time() - start < timeout:
    time.sleep(0.5)

if not wlan.isconnected():
    print("No se pudo conectar a WiFi")
else:
    print("WiFi conectado, IP:", wlan.ifconfig())

# ID cliente
client_id = b"pico_w_%d" % (time.ticks_ms() & 0xFFFF)

def connect_mqtt():
    client = MQTTClient(client_id, secrets.BROKER_IP, port=secrets.BROKER_PORT, keepalive=60)
    client.connect()
    print("Conectado al broker MQTT en", secrets.BROKER_IP)
    return client

try:
    mqtt = connect_mqtt()
except Exception as e:
    print("Error mqtt connect:", e)
    mqtt = None

count = 0
while True:
    if mqtt is None:
        try:
            mqtt = connect_mqtt()
        except Exception as e:
            print("Reintento MQTT:", e)
            time.sleep(5)
            continue
    payload = ujson.dumps({"estado": "conectado", "contador": count})
    try:
        mqtt.publish(b"robot/pico/estado", payload)
        print("Publicado:", payload)
    except Exception as e:
        print("Error publish:", e)
        mqtt = None
    count += 1
    time.sleep(5)
