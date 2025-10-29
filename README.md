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

Descarga la última UF2 de MicroPython para RPI_PICO_W desde la web oficial de MicroPython. (En la página de descargas están los UF2 y las instrucciones). 
[micropython.org](https://micropython.org/download/RPI_PICO_W/)

Con la Pico W desconectada: mantén presionado BOOTSEL, conecta por USB al RPi5, suéltalo — el dispositivo aparecerá como unidad USB llamada RPI-RP2.

Copia el archivo `.uf2` descargado al volumen RPI-RP2. La Pico W se reiniciará con MicroPython instalado.

(Alternativa: desde REPL `machine.bootloader()` si ya tienes acceso).

# 5) Código MicroPython para la Pico W (publicar cada 5 s)

Vamos a usar `umqtt.simple` (disponible en builds MicroPython)

## Instalación de la librería umqtt.simple

Si la librería `umqtt.simple` no está disponible en tu Pico W, puedes instalarla de dos formas:

### Opción A: Descargar manualmente y subir con Thonny

1. En tu navegador, abre el [repositorio oficial de MicroPython](https://github.com/micropython/micropython-lib/tree/master/umqtt.simple)

2. Descarga el archivo `umqtt/simple.py` y guárdalo localmente

3. Abre **Thonny** y conecta la Pico W

4. Ve a **Archivo → Guardar como → En el dispositivo**

5. Guárdalo en la ruta `/lib/umqtt/simple.py`
   
   > **Nota:** Si la carpeta `/lib` no existe, créala con clic derecho → "Nueva carpeta"

### Opción B: Instalar con mpremote (línea de comandos)

Si prefieres usar la terminal desde tu Raspberry Pi 5:

1. **Instala mpremote:**
   ```bash
   pip install mpremote
   ```

2. **Conecta la Pico W** por USB

3. **Instala la librería:**
   ```bash
   mpremote connect /dev/ttyACM0 mip install umqtt.simple
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

### Cómo subir main.py y secrets.py a la Pico W:

La forma más fácil desde el RPi5 es usar **Thonny** (IDE): Conecta la Pico W, en Thonny selecciona "MicroPython (Raspberry Pi Pico)" y sube los archivos `main.py` y `secrets.py` al dispositivo (guardar en device).

Igualmente puedes usar la siguiente alternativa:
usa `ampy` o `rshell` para copiar archivos:

```bash
# ejemplo con ampy (en RPi5)
pip3 install adafruit-ampy
ampy --port /dev/ttyACM0 put secrets.py
ampy --port /dev/ttyACM0 put main.py
```

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