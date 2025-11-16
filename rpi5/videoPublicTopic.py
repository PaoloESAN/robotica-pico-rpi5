import cv2
import numpy as np
import paho.mqtt.client as mqtt
import json
import os
import time
from ultralytics import YOLO

# --- Configuración MQTT ---
BROKER = "localhost"  # Cambia si tu broker está en otra IP
PORT = 1883
TOPIC = "robot/pico/estado" 

client = mqtt.Client()

try:
    client.connect(BROKER, PORT, 60)
    print(f"Conectado al broker MQTT en {BROKER}:{PORT}")
except Exception as e:
    print(f"Error al conectar con el broker MQTT: {e}")
    exit()

# --- Modelo YOLO ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(SCRIPT_DIR, "best.pt")
model = YOLO(model_path)

# --- Captura de cámara ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: no se pudo abrir la cámara")
    exit()

cv2.namedWindow("Detección en Cámara - Solo Pistachos", cv2.WINDOW_NORMAL)
print("Iniciando detección. Presiona 'q' para salir...")

frame_count = 0
PUB_EVERY_N_FRAMES = 5
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: no se pudo leer el frame de la cámara")
        break

    # Ejecutar la detección en el frame
    results = model(frame)

    # Dibujar solo los pistachos detectados
    annotated_frame = frame.copy()
    for result in results:
        boxes = result.boxes
        for box in boxes:
            class_name = result.names[int(box.cls)]
            if "pistachio" in class_name.lower():
                # Dibujar el bounding box
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Dibujar la confianza
                confidence = float(box.conf)
                cv2.putText(annotated_frame, f"{class_name} {confidence:.2f}", 
                           (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                # Publicar en MQTT cada N frames
                if frame_count % PUB_EVERY_N_FRAMES == 0:
                    msg = json.dumps({
                        "objeto": class_name,
                        "confianza": float(confidence)
                    })
                    result_pub = client.publish(TOPIC, msg)
                    if result_pub.rc == 0:
                        print(f"MQTT enviado a {TOPIC}: {msg}")
                    else:
                        print(f"Error al publicar en {TOPIC}")

    cv2.imshow("Detección en Cámara - Solo Pistachos", annotated_frame)
    frame_count += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client.disconnect()
print("Desconectado del broker MQTT")
