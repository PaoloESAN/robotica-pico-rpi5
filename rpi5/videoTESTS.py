from ultralytics import YOLO
import cv2
import os

# Obtener la ruta del directorio actual del script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construir la ruta relativa al modelo
model_path = os.path.join(script_dir, "best.pt")

# Cargar el modelo entrenado
model = YOLO(model_path)

# Inicializar la cámara (0 = cámara por defecto)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("No se pudo acceder a la cámara.")
    exit()

print("Cámara iniciada. Presiona 'q' para salir.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error al capturar el video")
        break

    # Ejecutar la detección en el frame
    results = model(frame)

    # Filtrar solo detecciones de pistachos
    filtered_results = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Obtener el nombre de la clase detectada
            class_name = result.names[int(box.cls)]
            # Solo agregar si es pistacho
            if "pistachio" in class_name.lower():
                filtered_results.append((box, class_name))
    
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

    cv2.imshow("Detección en tiempo real - Solo Pistachos", annotated_frame)

    # Salir al presionar 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar la cámara y cerrar ventanas
cap.release()
cv2.destroyAllWindows()