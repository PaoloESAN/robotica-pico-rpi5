# main.py (MicroPython para Pico W)
# Se conecta a WiFi, se suscribe al topic MQTT y envía señal serial al Arduino
# Conexiones:
# - Pico W GP4 (Pin 6) -> Level Converter LV1 -> Arduino RX
# - Pico W GP5 (Pin 7) -> Level Converter LV2 -> Arduino TX
import time
import network
import ujson
from umqtt.simple import MQTTClient
from machine import UART, Pin
import secrets

# Configurar UART para comunicación con Arduino
# UART(1): TX=GP4, RX=GP5
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
uart.init(bits=8, parity=None, stop=2)

# Conectar a WiFi
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

# ID cliente MQTT
client_id = b"pico_w_%d" % (time.ticks_ms() & 0xFFFF)

def send_command_to_arduino(command):
    """Envía un comando al Arduino por UART
    
    Args:
        command: String o bytes con el comando a enviar
    """
    try:
        if isinstance(command, str):
            command = command.encode()
        uart.write(command)
        print("Comando enviado al Arduino:", command)
    except Exception as e:
        print("Error enviando comando al Arduino:", e)

def check_arduino_response():
    """Verifica si hay respuesta del Arduino"""
    if uart.any():
        data = uart.read()
        if data:
            print("Respuesta del Arduino:", data)
            return data
    return None

def mqtt_callback(topic, msg):
    """Callback para procesar mensajes MQTT recibidos"""
    try:
        payload = ujson.loads(msg)
        print("Mensaje recibido en", topic.decode(), ":", payload)
        
        # Solo activar servo si el objeto detectado es "pistachio"
        if 'objeto' in payload and payload['objeto'].lower() == "pistachio":
            print("Pistacho detectado! Enviando señal al Arduino...")
            send_command_to_arduino(b'A')  # Enviar 'A' para ACTIVATE
            
            # Esperar respuesta del Arduino (con reintentos)
            timeout = 2000  # 2 segundos de timeout
            start_time = time.ticks_ms()
            response_received = False
            
            while time.ticks_ms() - start_time < timeout:
                response = check_arduino_response()
                if response == b'D':
                    print("Arduino confirmó: Secuencia completada")
                    response_received = True
                    break
                time.sleep(0.1)
            
            if not response_received:
                print("Advertencia: No se recibió confirmación del Arduino en 2s")
        else:
            print("Objeto no es pistacho, no se envía señal")
        
    except Exception as e:
        print("Error procesando mensaje:", e)

def connect_mqtt():
    """Conecta al broker MQTT y se suscribe al topic"""
    client = MQTTClient(client_id, secrets.BROKER_IP, port=secrets.BROKER_PORT, keepalive=60)
    client.set_callback(mqtt_callback)
    client.connect()
    print("Conectado al broker MQTT en", secrets.BROKER_IP)
    client.subscribe(b"robot/pico/estado")
    print("Suscrito al topic: robot/pico/estado")
    return client

# Inicializar conexión MQTT
try:
    mqtt = connect_mqtt()
except Exception as e:
    print("Error mqtt connect:", e)
    mqtt = None

# Loop principal
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

    # Esperar antes de volver a comprobar
    time.sleep(0.1)
