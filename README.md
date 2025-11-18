# 1) Instalar Docker en Raspberry Pi OS (RPi5)

### Actualiza
```bash
sudo apt update && sudo apt upgrade -y
```

### Descargar e instala docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

# 2) Preparar Mosquitto (broker MQTT) en Docker

### Crea una carpeta en el RPi5 para la configuración y datos:

```bash
mkdir -p ~/mosquitto/{config,data,log}
cd ~/mosquitto
```

Crea un archivo `mosquitto.conf` mínimo (modo desarrollo — permite conexiones anónimas en LAN). Guarda en `~/mosquitto/config/mosquitto.conf`:

```conf
# mosquitto.conf mínimo para pruebas
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
```

Ahora lanza el contenedor oficial (multi-arch) exponiendo el puerto 1883:

```bash
# desde ~/mosquitto
sudo docker pull eclipse-mosquitto:latest

sudo docker run -d \
  --name mosquitto \
  --restart unless-stopped \
  -p 1883:1883 \
  -v $(pwd)/config:/mosquitto/config \
  -v $(pwd)/data:/mosquitto/data \
  -v $(pwd)/log:/mosquitto/log \
  eclipse-mosquitto:latest
```

Esto publica el puerto 1883 del broker al mismo puerto en la RPi5.

Verifica que está corriendo: `sudo docker ps` (verás eclipse-mosquitto).

Ver logs con: `sudo docker logs mosquitto` o mirar `~/mosquitto/log/mosquitto.log`.

(eclipse-mosquitto en Docker Hub es la imagen oficial y soporta multi-arquitecturas, incluida ARM.)

# 3) Averigua la IP local de tu RPi5 (para que la Pico W la use)

En la RPi5 ejecuta:

```bash
hostname -I
# o
ip addr show wlan0   # si el RPi5 está en Wi-Fi
ip addr show eth0    # o en cable Ethernet
```

Anota la IP (ej. `192.168.1.42`). La Pico W deberá publicar hacia esa IP (broker). Si tu RPi5 usa localhost para el cliente host, úsalo en el script host; desde la Pico W debe usarse la IP real en la LAN.

# 4) Flashear MicroPython en la Raspberry Pi Pico W

La forma más sencilla de instalar MicroPython en tu Pico W es usando **Thonny**:

1. **Abre Thonny** (si no lo tienes instalado: `sudo apt install thonny` en RPi5, o descárgalo desde [thonny.org](https://thonny.org) en Windows)

2. **Conecta la Pico W** por USB a tu computadora

3. En la **esquina inferior derecha** de Thonny, haz clic donde dice el intérprete actual (por ejemplo, "Local Python 3")

4. Selecciona **"MicroPython (Raspberry Pi Pico)"** o **"Configure interpreter..."**

5. Aparecerá una ventana de configuración. Si MicroPython no está instalado:
   - Haz clic en **"Install or update MicroPython"**
   - Selecciona tu modelo: **"Raspberry Pi Pico W"**
   - Haz clic en **"Install"**
   - Espera a que se complete la instalación

6. Una vez instalado, verás en la consola de Thonny el prompt `>>>` de MicroPython

> **Nota:** Si la Pico W no aparece, intenta mantener presionado el botón **BOOTSEL** mientras la conectas por USB.

# 5) Código MicroPython para la Pico W (publicar cada 5 s)

Vamos a usar `umqtt.simple` (disponible en builds MicroPython)

## Instalación de la librería umqtt.simple

Si la librería `umqtt.simple` no está disponible en tu Pico W, puedes instalarla de dos formas:

### Instalar con mpremote (línea de comandos)

Si prefieres usar la terminal desde tu Raspberry Pi 5 o windows:

1. **Instala mpremote:**
   ```bash
   pip install mpremote
   ```

2. **Conecta la Pico W** por USB

3. **Instala la librería:**
   ```bash
   mpremote connect /dev/ttyACM0 mip install umqtt.simple
   ```

   Alternativa si estas en windows(reemplazar COM10 por otro si es necesario, esto se puede visualizar en administrador de dispositivos, luego en ver: ver dispositivos ocultos(conectar la rasberry pi pico w de manera normal sin presionar el boton))
   ```bash
   mpremote connect COM10 mip install umqtt.simple
   ```

   > **Nota:** `mip` es el gestor de paquetes de MicroPython (similar a `pip`)

### Verificar la instalación

En la consola de Thonny, ejecuta:

```python
import umqtt.simple
print("MQTT OK")
```

Si no hay errores, la librería está lista para usar.

## Sobre el archivo main.py

El archivo `main.py` se encuentra en la carpeta `/picow` y hace lo siguiente:

- Conecta a Wi-Fi
- Conecta al broker en la IP del RPi5
- Publica `{"estado":"conectado"}` cada 5 segundos en `robot/pico/estado`

## ⚠️ Configurar el archivo secrets.py

El archivo `secrets.py` contiene **tus credenciales personales** de Wi-Fi y la dirección del broker MQTT. 

**IMPORTANTE:** Debes editar este archivo con tus propios datos antes de subirlo a la Pico W.

Ejemplo del contenido de `secrets.py`:

```python
# secrets.py - Credenciales de red (EDITAR CON TUS DATOS)
WIFI_SSID = "TU_NOMBRE_DE_WIFI"        # ← Cambiar por el nombre de tu red Wi-Fi
WIFI_PASSWORD = "TU_CONTRASEÑA_WIFI"    # ← Cambiar por tu contraseña Wi-Fi
MQTT_BROKER = "192.168.1.42"            # ← Cambiar por la IP de tu RPi5 (ver paso 3)
```

### Cómo subir main.py y secrets.py a la Pico W:

**Antes de continuar, asegúrate de haber editado `secrets.py` con tus credenciales.**

La forma más fácil desde el RPi5 es usar **Thonny** (IDE): Conecta la Pico W, en Thonny selecciona "MicroPython (Raspberry Pi Pico)" y sube los archivos `main.py` y `secrets.py` al dispositivo (guardar en device).

### Opción alternativa: Subir archivos con mpremote

**Recuerda editar `secrets.py` con tus credenciales antes de copiar los archivos.**

Si prefieres usar la terminal desde tu Raspberry Pi 5:

```bash
# Instala mpremote
pip3 install mpremote

# Copia los archivos a la Pico W (asegúrate de estar en la carpeta correcta)
mpremote connect /dev/ttyACM0 fs cp secrets.py :secrets.py
mpremote connect /dev/ttyACM0 fs cp main.py :main.py
```

Si estás en Windows, usa `COM10` u otro puerto en lugar de `/dev/ttyACM0`.
Se puede ver esto en Administrador de dispositivos, luego en Ver → Dispositivos ocultos (conectar la Raspberry Pi Pico W sin presionar el botón BOOTSEL).

> **Nota:** El `:` antes del nombre del archivo indica que se copiará a la raíz del sistema de archivos de la Pico W.

# 6) Script Python en RPi5 (host) que se suscribe al topic

En la RPi5 (host, no dentro del contenedor), crea un entorno y usa `paho-mqtt`:

```bash
sudo apt update
sudo apt install -y python3-pip
pip3 install paho-mqtt
```

Luego descarga el archivo dentro de la carpeta `/rpi5` llamado `subscriber.py`

Ejecuta:

```bash
python3 subscriber.py
```

Deberías ver los JSON publicados por la Pico W imprimiéndose en la terminal cuando la Pico publique cada 5 segundos.

# 7) Pruebas auxiliares (cliente de línea de comandos)

En la RPi5 puedes instalar los clientes Mosquitto y usarlos para probar la conexión:

```bash
sudo apt install -y mosquitto-clients

# Suscribirse (en una terminal)
mosquitto_sub -h localhost -p 1883 -t robot/pico/estado -v

# Publicar manualmente (otra terminal)
mosquitto_pub -h localhost -p 1883 -t robot/pico/estado -m '{"test":"hola"}'
```

Si `mosquitto_sub` recibe mensajes, el broker funciona y la red está bien configurada. (Si deseas probar desde otra máquina en la misma LAN, cambia `-h localhost` por la IP de la RPi5).

---

# 8) Detección de objetos con cámara usando MobileNet SSD

Esta sección explica cómo usar la cámara en el RPi5 para detectar objetos localmente usando OpenCV y MobileNet SSD.

## Paso 1: Instalar dependencias en RPi5

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-opencv python3-pip
pip3 install opencv-python paho-mqtt numpy torch torchvision
```

### Librerías necesarias y sus propósitos:

- **opencv-python (cv2)**: Captura de video y procesamiento de imágenes
- **paho-mqtt**: Cliente MQTT para publicar detecciones al broker
- **numpy**: Operaciones matriciales y procesamiento de arrays
- **torch**: Framework de deep learning (PyTorch) para ejecutar el modelo VGG16
- **torchvision**: Utilidades de PyTorch para visión por computadora (transformaciones de imágenes y modelos pre-entrenados)

> **Nota:** La instalación de PyTorch puede tardar varios minutos en Raspberry Pi 5. Si prefieres una instalación más ligera, puedes usar:
> ```bash
> pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu
> ```

## Paso 2: Descargar modelo de detección de pistachos

**IMPORTANTE:** El modelo de pistachos (`modelo_pistachos.pth`) es demasiado grande para incluirlo en GitHub. Debes descargarlo manualmente:

1. **Accede a la carpeta de Google Drive:**
   
   [Descargar modelo_pistachos.pth desde Google Drive](https://drive.google.com/drive/folders/1814wg9bwC7ZVNoGwz1JBUcgwl99mGPQg?usp=sharing)

2. **Descarga el archivo `modelo_pistachos.pth`**

3. **Coloca el archivo descargado en la carpeta `/rpi5`** del proyecto:
   ```
   robotica-final/
   └── rpi5/
       ├── InspectionVideoSystem.py
       ├── modelo_pistachos.pth  ← Aquí debe estar
       ├── MobileNetSSD_deploy.prototxt
       └── MobileNetSSD_deploy.caffemodel
   ```

## Paso 3: Archivos del modelo MobileNet SSD

Los archivos del modelo MobileNet SSD ya están incluidos en la carpeta `/rpi5` del proyecto:
- `MobileNetSSD_deploy.prototxt` — Arquitectura del modelo
- `MobileNetSSD_deploy.caffemodel` — Pesos pre-entrenados

**No es necesario descargar nada adicional para MobileNet SSD.**

## Paso 4: Script de detección con cámara

El script `InspectionVideoSystem.py` en la carpeta `/rpi5` realiza:
- Captura de video desde la cámara del RPi5
- Detección de pistachos en tiempo real usando VGG16 + OpenCV
- Publicación de detecciones al broker MQTT en formato JSON:
  ```json
  {
    "objeto": "pistacho",
    "confianza": 0.95
  }
  ```

Para ejecutarlo:

```bash
cd ~/rpi5
python3 InspectionVideoSystem.py
```

o usando Thonny.

**Presiona 'q' para detener la detección.**

---

## Conexión del servomotor (MG946R / servos típicos)

Esta sección explica cómo conectar un servomotor típico (cable rojo, marrón y amarillo/ naranja) a la Raspberry Pi Pico W.

- **Colores típicos del cable:**
   - `Rojo`  : VCC (alimentación del servo) — normalmente +5V
   - `Marrón`: GND (masa)
   - `Amarillo/ Naranja`: Señal PWM (entrada de control)

- **Conexión recomendada para la Pico W:**
   - `Servo Rojo`  -> `VBUS` (40) del pico W, solo funciona si el pico W esta conectado por USB
   - `Servo Marrón`-> `GND` (38) del pico W
   - `Servo Amarillo` -> `GP15` (20) del Pico W
- **Imagen Referencial**
   -
    <img width="842" height="596" alt="picow-pinout" src="https://github.com/user-attachments/assets/1090c2b2-0a6c-492f-bce1-2a369d17d361" />

- **Notas importantes y recomendaciones:**
   - Los servos como el **MG946R** pueden consumir picos de corriente elevados al moverse. Usa una fuente de 5V capaz de suministrar corriente suficiente (por ejemplo 2–3 A o más, según el servo y la carga).
   - Nunca alimentes servos de potencia significativa directamente desde la salida 3.3V de la Pico W. Usa una fuente 5V separada.
   - Conectar las masas (GND) de la fuente 5V y de la Pico W es obligatorio para que la señal PWM sea referenciada correctamente.
   - Añade un condensador de desacoplo (por ejemplo 470 µF–1000 µF, 16V) entre `5V` y `GND` cerca del conector del servo para suavizar picos de corriente.
   - Si el servo se comporta de forma errática, considera añadir un diodo de protección o un circuito de filtrado, y revisa que la fuente entregue suficiente corriente.
   - La mayoría de servos aceptan señal de 3.3V como lógica para el pin de señal; si tienes dudas, consulta la hoja de datos del servo o usa un conversor de nivel lógico.

Ejemplo de conexión (resumen):

 - `Fuente 5V (+)`  -> `Servo Rojo`
 - `Fuente GND (-)` -> `Servo Marrón` AND `Pico W GND` (conectar ambas masas)
 - `Pico W GP15`    -> `Servo Amarillo` (señal PWM)


## Enlace a recursos adicionales

Todos los archivos grandes y recursos adicionales del proyecto están disponibles en:

[Google Drive - Recursos del Proyecto](https://drive.google.com/drive/folders/1814wg9bwC7ZVNoGwz1JBUcgwl99mGPQg?usp=sharing)
Siguiendo lo anterior evitarás problemas de suministro y referencia entre la Pico W y el servo.
