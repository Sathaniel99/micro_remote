"""Pequeño cliente de línea para transmitir audio por UDP.

Este script se usa para pruebas rápidas desde la consola: lee el micrófono
y envía paquetes UDP al receptor. Diseñado para uso local o en LAN.

No modifica la lógica principal — solo documentación y mensajes.
"""

import pyaudio
import socket
import time
from utils import obtener_ip_local, IP_enlazadas

# Configuración de audio
CHUNK = 1024  # Tamaño del buffer (ajusta según latencia/calidad)
FORMAT = pyaudio.paInt16  # Formato de audio
CHANNELS = 1  # Mono
RATE = 44100  # Frecuencia de muestreo (Hz)

# Configuración de red
HOST_RECEPTOR = "169.254.23.244"
PORT = 5000

print(f"Preparando transmisión a {HOST_RECEPTOR}:{PORT}...")
print("(Info) Espera 5 segundos para liberar el micrófono si hace falta...")

# Espera 5 segundos antes de iniciar
for i in range(5, 0, -1):
    print(f"Iniciando en {i} segundos...", end="\r")
    time.sleep(1)
print("\n¡Transmisión iniciada!                          ")

# Inicializa PyAudio
p = pyaudio.PyAudio()

# Abre el micrófono
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK
)

# Configura el socket UDP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    print(f"Enviando audio a {HOST_RECEPTOR}:{PORT}...")
    while True:
        data = stream.read(CHUNK)  # Lee el audio del micrófono
        s.sendto(data, (HOST_RECEPTOR, PORT))  # Envía el audio por UDP
except KeyboardInterrupt:
    print("\nDeteniendo el servidor...")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    s.close()
