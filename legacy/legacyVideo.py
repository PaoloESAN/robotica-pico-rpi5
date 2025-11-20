import cv2
import numpy as np
import paho.mqtt.client as mqtt
import json
import os
import time

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

# --- Modelo MobileNet SSD ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
net = cv2.dnn.readNetFromCaffe(
    os.path.join(SCRIPT_DIR, "MobileNetSSD_deploy.prototxt"),
    os.path.join(SCRIPT_DIR, "MobileNetSSD_deploy.caffemodel")
)

CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant",
           "sheep", "sofa", "train", "tvmonitor"]

# --- Captura de cámara ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: no se pudo abrir la cámara")
    exit()

cv2.namedWindow("Detección en Cámara", cv2.WINDOW_NORMAL)
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

    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
                                 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            idx = int(detections[0, 0, i, 1])
            if idx >= len(CLASSES):
                continue
            label = CLASSES[idx]

            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
            cv2.putText(frame, f"{label}: {confidence:.2f}",
                        (startX, startY - 5), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 255, 0), 2)

            if frame_count % PUB_EVERY_N_FRAMES == 0:
                msg = json.dumps({
                    "objeto": label,
                    "confianza": float(confidence)
                })
                result = client.publish(TOPIC, msg)
                if result.rc == 0:
                    print(f"MQTT enviado a {TOPIC}: {msg}")
                else:
                    print(f"Error al publicar en {TOPIC}")

    cv2.imshow("Detección en Cámara", frame)
    frame_count += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client.disconnect()
print("Desconectado del broker MQTT")
