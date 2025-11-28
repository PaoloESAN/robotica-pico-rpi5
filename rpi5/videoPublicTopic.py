import cv2
import numpy as np
import paho.mqtt.client as mqtt
import json
import os
import time
import serial # Importar librería para comunicación serial
from ultralytics import YOLO

# --- Configuración Arduino (Serial) ---
# CAMBIA 'COM3' POR EL PUERTO DE TU ARDUINO
SERIAL_PORT = 'COM18'
BAUD_RATE = 9600
arduino = None

try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) # Esperar a que el Arduino se reinicie al conectar
    print(f"Conectado al Arduino en {SERIAL_PORT}")
except Exception as e:
    print(f"No se pudo conectar al Arduino: {e}")
    print("El programa continuará sin mover el servo.")

# Variables para controlar el tiempo del servo (evitar spam de comandos)
last_servo_time = 0
servo_cooldown = 3 # Segundos de espera entre movimientos (ajusta según la velocidad de tu servo)

# --- Configuración MQTT ---
BROKER = "172.17.144.102" # Cambia por la IP de tu broker MQTT
PORT = 1883
TOPIC = "robot/pico/estado"

client = mqtt.Client()

try:
    client.connect(BROKER, PORT, 60)
    print(f"Conectado al broker MQTT en {BROKER}:{PORT}")
except Exception as e:
    print(f"Error al conectar con el broker MQTT: {e}")
    # No hacemos exit() aquí para permitir que la cámara funcione aunque falle MQTT

# --- Modelo YOLO ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Asegúrate de que best.pt exista, si no usa yolov8n.pt para probar
model_path = os.path.join(SCRIPT_DIR, "best.pt")
model = YOLO(model_path)

# --- Captura de cámara ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: no se pudo abrir la cámara")
    exit()

cv2.namedWindow("Detección", cv2.WINDOW_NORMAL)
print("Iniciando detección. Presiona 'q' para salir...")

frame_count = 0
PUB_EVERY_N_FRAMES = 5
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: no se pudo leer el frame")
        break

    results = model(frame)
    annotated_frame = frame.copy()
   
    pistachio_detected = False # Bandera para saber si vimos uno en este frame

    for result in results:
        boxes = result.boxes
        for box in boxes:
            class_name = result.names[int(box.cls)]
           
            # Filtramos por "pistachio"
            if "pistachio" in class_name.lower():
                pistachio_detected = True
               
                # Dibujar bounding box
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                confidence = float(box.conf)
                cv2.putText(annotated_frame, f"{class_name} {confidence:.2f}",
                           (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                # Publicar MQTT
                if frame_count % PUB_EVERY_N_FRAMES == 0:
                    msg = json.dumps({"objeto": class_name, "confianza": confidence})
                    client.publish(TOPIC, msg)

    # --- Lógica del Servo ---
    # Si detectamos un pistacho Y ha pasado el tiempo de enfriamiento
        # --- Lógica del Servo ---
        # --- Lógica del Servo ---
        current_time = time.time()
        if pistachio_detected and confidence > 0.80 and (current_time - last_servo_time > servo_cooldown):
            if arduino and arduino.is_open:
                try:
                    print(f"¡Pistacho detectado con {confidence:.2f} de confianza! Moviendo servo...")
                    arduino.write(b'1')  # Enviar comando al Arduino
                    last_servo_time = current_time
                except Exception as e:
                    print(f"Error enviando datos al Arduino: {e}")

    cv2.imshow("Detección", annotated_frame)
    frame_count += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client.disconnect()
if arduino:
    arduino.close()
print("Sistema apagado")