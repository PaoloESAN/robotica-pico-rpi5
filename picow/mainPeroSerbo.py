# main.py (MicroPython para Pico W)
import time
import network
import ujson
from umqtt.simple import MQTTClient
from machine import Pin, PWM
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

# Configurar servomotor en pin GPIO 15
servo_pin = PWM(Pin(15))
servo_pin.freq(50)  # Frecuencia de 50 Hz para servomotor estándar

def set_servo_angle(angle):
    """Mueve el servomotor a un ángulo específico (0-180 grados)"""
    # Convertir ángulo a duty cycle (1000-9000 para rango 0-180 grados)
    duty = int(1000 + (angle / 180) * 8000)
    servo_pin.duty_u16(duty)
    print("Servomotor movido a:", angle, "grados")

# ID cliente
client_id = b"pico_w_%d" % (time.ticks_ms() & 0xFFFF)

def receive_json_from_broker(msg):
    """Recibe un mensaje JSON del broker y lo procesa
    
    Args:
        msg: Mensaje en bytes del broker
        
    Returns:
        dict: Diccionario con el JSON parseado, o None si hay error
    """
    try:
        payload = ujson.loads(msg)
        print("JSON recibido del broker:", payload)
        return payload
    except Exception as e:
        print("Error al parsear JSON:", e)
        return None

def mqtt_callback(topic, msg):
    """Callback para procesar mensajes MQTT recibidos"""
    try:
        payload = ujson.loads(msg)
        print("Mensaje recibido en", topic, ":", payload)
        
        # Buscar campo 'angulo' en el payload
        if 'angulo' in payload:
            angle = int(payload['angulo'])
            # Asegurar que el ángulo esté en rango válido (0-180)
            angle = max(0, min(180, angle))
            set_servo_angle(angle)
    except Exception as e:
        print("Error procesando mensaje:", e)

def connect_mqtt():
    client = MQTTClient(client_id, secrets.BROKER_IP, port=secrets.BROKER_PORT, keepalive=60)
    client.set_callback(mqtt_callback)
    client.connect()
    print("Conectado al broker MQTT en", secrets.BROKER_IP)
    client.subscribe(b"robot/deteccion/ia")  # Subscribirse al topic de detección de IA
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
    
    # Procesar mensajes MQTT recibidos
    try:
        mqtt.check_msg()
    except Exception as e:
        print("Error checking messages:", e)
        mqtt = None
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
