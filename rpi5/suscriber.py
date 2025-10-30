# subscriber.py (actualizado para ambos topics)
import paho.mqtt.client as mqtt
import json

BROKER_IP = "localhost"
BROKER_PORT = 1883
TOPIC_PICO = "robot/pico/estado"
TOPIC_IA = "robot/deteccion/ia"


def on_connect(client, userdata, flags, rc):
    print(f"Conectado al broker con código: {rc}")
    client.subscribe([(TOPIC_PICO, 0), (TOPIC_IA, 0)])
    print(f"Suscrito a: {TOPIC_PICO} y {TOPIC_IA}")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"\n[{topic}] Recibido: {payload}")

    try:
        data = json.loads(payload)
        if topic == TOPIC_IA:
            print(
                f" DETECCIÓN AI: {data['objeto']} con {data['confianza']*100}% confianza")
        elif topic == TOPIC_PICO:
            print(f" Pico W: {data}")
    except json.JSONDecodeError:
        print(f" No es JSON válido")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_IP, BROKER_PORT, 60)
print("Esperando mensajes... (Ctrl+C para salir)")

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\nDesconectando...")
    client.disconnect()