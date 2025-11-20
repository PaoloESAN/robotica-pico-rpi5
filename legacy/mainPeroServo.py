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
servo_pin_obj = Pin(15)
servo_pwm = PWM(servo_pin_obj)
servo_pwm.freq(50)  # 50 Hz típico para servos

# Ajustes para MG946R
min_pulse = 500         # microsegundos = 0 grados
max_pulse = 2500        # microsegundos = 180 grados

def pulse_to_duty_u16(pulse_us):
    """Convierte microsegundos de pulso a duty_u16"""
    periodo_us = int(1_000_000 / 50)   # 20000 para 50 Hz
    duty = int(pulse_us / periodo_us * 65535)
    if duty < 0:
        duty = 0
    elif duty > 65535:
        duty = 65535
    return duty

def angle_to_pulse(angle):
    """Convierte ángulo (0-180) a microsegundos de pulso"""
    if angle < 0:
        angle = 0
    if angle > 180:
        angle = 180
    pulse = min_pulse + (angle / 180.0) * (max_pulse - min_pulse)
    return int(pulse)

def set_servo_angle(angle):
    """Mueve el servomotor a un ángulo específico (0-180 grados)"""
    pulse = angle_to_pulse(angle)
    duty = pulse_to_duty_u16(pulse)
    servo_pwm.duty_u16(duty)
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
        
        # Solo activar servo si el objeto detectado es "pistachio"
        if 'objeto' in payload and payload['objeto'].lower() == "pistachio":
            print("Pistacho detectado! Activando servo...")
            # Realizar secuencia de movimiento: 0 -> 90 -> 180 -> 0
            set_servo_angle(0)
            time.sleep(0.5)
            set_servo_angle(90)
            time.sleep(0.5)
            set_servo_angle(180)
            time.sleep(0.5)
            set_servo_angle(0)
        else:
            print("Objeto no es pistacho, servo no se activa")
        
    except Exception as e:
        print("Error procesando mensaje:", e)

def connect_mqtt():
    client = MQTTClient(client_id, secrets.BROKER_IP, port=secrets.BROKER_PORT, keepalive=60)
    client.set_callback(mqtt_callback)
    client.connect()
    print("Conectado al broker MQTT en", secrets.BROKER_IP)
    client.subscribe(b"robot/pico/estado")   # Subscribirse al topic de estado para mover servo
    return client

try:
    mqtt = connect_mqtt()
except Exception as e:
    print("Error mqtt connect:", e)
    mqtt = None

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

    # Solo escuchar; esperar un momento antes de volver a comprobar
    time.sleep(1)
