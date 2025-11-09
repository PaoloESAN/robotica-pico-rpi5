import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
from torchvision import transforms
import os
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, "modelo_pistachos.pth")

device = torch.device("cpu")
print(f"Usando dispositivo: {device}\n")

class VGG16Custom(nn.Module):
    def __init__(self):
        super(VGG16Custom, self).__init__()
        vgg16 = models.vgg16(weights=None)
        self.features = vgg16.features
        self.avgpool = vgg16.avgpool
        self.classifier = nn.Sequential(
            nn.Linear(512 * 7 * 7, 2048),
            nn.ReLU(True),
            nn.Dropout(0.5),
            nn.Linear(2048, 512),
            nn.ReLU(True),
            nn.Dropout(0.5),
            nn.Linear(512, 2),
            nn.LogSoftmax(dim=1)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x

try:
    print(f"Cargando modelo VGG16...")
    model = VGG16Custom()
    checkpoint = torch.load(MODEL_PATH, map_location=device)
    
    new_state_dict = {}
    for k, v in checkpoint.items():
        if k.startswith("classifier."):
            if "fc1" in k:
                new_key = k.replace("classifier.fc1", "classifier.0")
            elif "fc2" in k:
                new_key = k.replace("classifier.fc2", "classifier.3")
            elif "fc3" in k:
                new_key = k.replace("classifier.fc3", "classifier.6")
            else:
                new_key = k
            new_state_dict[new_key] = v
        else:
            new_state_dict[k] = v
    
    model.load_state_dict(new_state_dict, strict=False)
    model = model.to(device)
    model.eval()
    print("✓ Modelo cargado correctamente\n")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                       std=[0.229, 0.224, 0.225])
])

torch.set_num_threads(4)
torch.set_grad_enabled(False)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

cv2.namedWindow("Detección Pistachos", cv2.WINDOW_NORMAL)
print("Iniciando detección. Presiona 'q' para salir...\n")

frame_count = 0
detection_count = 0
last_print = time.time()
skip_frames = 0
MAX_DETECTIONS_PER_FRAME = 3
process_every_n_frames = 3
fps_start_time = time.time()
fps_frame_count = 0
current_fps = 0
last_detections = []
batch_processing = True

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    skip_frames += 1
    
    cap.grab()
    
    frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    lower_brown = np.array([5, 50, 50])
    upper_brown = np.array([35, 255, 255])
    
    mask = cv2.inRange(frame_hsv, lower_brown, upper_brown)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:MAX_DETECTIONS_PER_FRAME]
    
    frame_detections = 0
    current_frame_detections = []
    
    if skip_frames >= process_every_n_frames:
        regions_to_process = []
        region_coords = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 200 < area < 50000:
                x, y, w, h = cv2.boundingRect(contour)
                
                y1 = max(0, y - 5)
                y2 = min(frame.shape[0], y + h + 5)
                x1 = max(0, x - 5)
                x2 = min(frame.shape[1], x + w + 5)
                
                region = frame[y1:y2, x1:x2]
                
                if region.shape[0] > 20 and region.shape[1] > 20:
                    try:
                        img_pil = transforms.ToPILImage()(region)
                        img_tensor = transform(img_pil)
                        regions_to_process.append(img_tensor)
                        region_coords.append((x1, y1, x2, y2))
                    except:
                        pass
        
        if regions_to_process:
            try:
                batch_tensor = torch.stack(regions_to_process).to(device)
                
                with torch.no_grad():
                    outputs = model(batch_tensor)
                    probs = torch.softmax(outputs, dim=1)
                
                for i, (x1, y1, x2, y2) in enumerate(region_coords):
                    confidence = probs[i, 1].item()
                    
                    if confidence > 0.5:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"Pistacho: {confidence:.2f}", (x1, y1 - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                        frame_detections += 1
                        detection_count += 1
                        current_frame_detections.append((x1, y1, x2, y2, confidence))
            except:
                pass
        
        if current_frame_detections:
            last_detections = current_frame_detections
    else:
        if last_detections:
            for x1, y1, x2, y2, conf in last_detections:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 0), 2)
                cv2.putText(frame, f"Pistacho: {conf:.2f}", (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 200, 0), 1)
        else:
            for contour in contours:
                area = cv2.contourArea(contour)
                if 200 < area < 50000:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    y1 = max(0, y - 5)
                    y2 = min(frame.shape[0], y + h + 5)
                    x1 = max(0, x - 5)
                    x2 = min(frame.shape[1], x + w + 5)
                    
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                    cv2.putText(frame, "Candidato", (x1, y1 - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1)
    
    if skip_frames >= process_every_n_frames:
        skip_frames = 0
    
    fps_frame_count += 1
    elapsed_time = time.time() - fps_start_time
    if elapsed_time > 1.0:
        current_fps = fps_frame_count / elapsed_time
        fps_frame_count = 0
        fps_start_time = time.time()
    
    cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 25),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, f"Detectados: {frame_detections}", (10, 50),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, f"Total: {detection_count}", (10, 75),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    cv2.imshow("Detección Pistachos", frame)
    
    if time.time() - last_print > 2:
        print(f"Frame {frame_count} - Pistachos detectados este frame: {frame_detections} - FPS: {current_fps:.1f}")
        last_print = time.time()
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print(f"\nTotal de frames procesados: {frame_count}")
print(f"Total de pistachos detectados: {detection_count}")
