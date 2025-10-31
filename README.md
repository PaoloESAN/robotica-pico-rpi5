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

# 8) Detección de objetos con cámara usando TensorFlow Lite

Esta sección explica cómo usar la cámara en el RPi5 para detectar objetos localmente usando TensorFlow Lite y MobileNet SSD.

## Paso 1: Instalar dependencias en RPi5

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar OpenCV y otras librerías
sudo apt install -y python3-opencv python3-pip
pip3 install opencv-python tflite-runtime paho-mqtt numpy pillow
```

> **Nota:** Si `tflite-runtime` da problemas durante la instalación, prueba con:
> ```bash
> pip3 install --extra-index-url https://google-coral.github.io/py-repo/ tflite_runtime
> ```

## Paso 2: Descargar modelo pre-entrenado (MobileNet SSD v1)

Este modelo es ligero y rápido, ideal para dispositivos como Raspberry Pi.

```bash
# Crear carpeta para el modelo
mkdir -p ~/ai_detection
cd ~/ai_detection

# Descargar MobileNet SSD v1 (optimizado para TensorFlow Lite)
wget https://storage.googleapis.com/download.tensorflow.org/models/tflite/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip
unzip coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip

# Descargar archivo de etiquetas (COCO dataset)
wget https://raw.githubusercontent.com/tensorflow/models/master/research/object_detection/data/mscoco_label_map.pbtxt -O labelmap.txt
```

Después de este paso, deberías tener en `~/ai_detection/`:
- `detect.tflite` — Modelo de detección
- `labelmap.txt` — Etiquetas de objetos detectables (persona, auto, perro, etc.)

## Paso 3: Script de detección con cámara

El script `InspectionVideoSystem.py` en la carpeta `/rpi5` realiza:
- Captura de video desde la cámara del RPi5
- Detección de objetos en tiempo real usando TensorFlow Lite
- Publicación de detecciones al broker MQTT (opcional)

Para ejecutarlo:

```bash
cd ~/rpi5
python3 InspectionVideoSystem.py
```

o usando Thonny.