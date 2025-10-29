# subscriber.py (RPi5 host)
import paho.mqtt.client as mqtt

BROKER = "localhost"   # o la IP local, por ejemplo 127.0.0.1
PORT = 1883
TOPIC = "robot/pico/estado"

def on_connect(client, userdata, flags, rc):
    print("Conectado al broker, rc:", rc)
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    print("Recibido:", msg.topic, msg.payload.decode())

client = mqtt.Client("rpi5_subscriber")
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_forever()
