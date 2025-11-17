import pyaudio
import socket
import numpy as np  # Para manipular los datos de audio

# Configuración de audio
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Configuración de red
HOST = '0.0.0.0'  # Escucha en todas las interfaces de red
PORT = 5000

# Factor de amplificación (1.0 = sin cambio, 2.0 = doble volumen, etc.)
AMPLIFICATION_FACTOR = 2.0

# Inicializa PyAudio
p = pyaudio.PyAudio()

# Abre el stream de salida
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    output=True,
    frames_per_buffer=CHUNK
)

# Configura el socket UDP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((HOST, PORT))

print(f"Escuchando audio en {HOST}:{PORT}...")
print("Presiona Ctrl+C para detener el script...")

try:
    while True:
        data, _ = s.recvfrom(4096)  # Recibe datos UDP

        # Convierte los datos a un array de numpy (formato int16)
        audio_data = np.frombuffer(data, dtype=np.int16)

        # Amplifica el audio (multiplica por el factor)
        amplified_audio = np.clip(audio_data * AMPLIFICATION_FACTOR, -32768, 40000).astype(np.int16)

        # Convierte de vuelta a bytes
        amplified_data = amplified_audio.tobytes()

        # Reproduce el audio amplificado
        stream.write(amplified_data)
except KeyboardInterrupt:
    print("\nDeteniendo el cliente...")
except Exception as e:
    print(f"\nError inesperado: {e}")
finally:
    # Cierra el stream y PyAudio
    if stream.is_active():
        stream.stop_stream()
    stream.close()
    p.terminate()
    # Cierra el socket
    s.close()
    print("Recursos liberados correctamente.")
