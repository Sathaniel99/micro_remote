"""
interface_emisor.py - Interfaz de transmisión de audio UDP

Requiere:
- pyaudio: captura de audio del micrófono
- common.py: estilos compartidos y utilidades UI
- utils.py: mapeo de IPs (opcional)
"""

import pyaudio
import socket
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import sys

from common import (
    AUDIO_CONFIG, COLORS, setup_style, create_plot, 
    center_window, configure_window
)

# Simulación de IP_enlazadas si no está disponible
try:
    from utils import IP_enlazadas
except ImportError:
    IP_enlazadas = {
        "localhost": "127.0.0.1",
        "local": "0.0.0.0"
    }


class AudioTransmitterApp:
    def __init__(self, root):
        self.root = root
        
        # Configurar ventana base
        configure_window(self.root, "Transmisor de Audio UDP", icon_name="emisor.ico")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Configuración de audio
        self.CHUNK = AUDIO_CONFIG["CHUNK"]
        self.FORMAT = AUDIO_CONFIG["FORMAT"]
        self.CHANNELS = AUDIO_CONFIG["CHANNELS"]
        self.RATE = AUDIO_CONFIG["RATE"]

        # Variables de control
        self.HOST_RECEPTOR = tk.StringVar()
        self.AMPLIFICATION_FACTOR = tk.DoubleVar(value=1.0)
        self.transmitting = False
        self.transmit_event = threading.Event()
        
        # Recursos de audio/red
        self.p = None
        self.stream = None
        self.s = None
        self.PORT = 5000

        # Buffer para gráfico
        self.audio_buffer = np.zeros(self.CHUNK)

        # Setup UI con estilos compartidos
        setup_style()
        self.setup_ui()

    def get_available_ips(self):
        """Obtiene lista de IPs disponibles desde utils o defaults."""
        if isinstance(IP_enlazadas, dict):
            return list(IP_enlazadas.values())
        elif isinstance(IP_enlazadas, list):
            return IP_enlazadas
        else:
            return ["127.0.0.1", "192.168.1.1"]

    def get_local_ips(self):
        """
        Obtiene las direcciones IP locales del dispositivo.
        Retorna una lista con las IPs disponibles.
        """
        try:
            hostname = socket.gethostname()
            hostname_ex = socket.gethostbyname_ex(hostname)
            ips = hostname_ex[2]
            return ips if ips else ["No disponible"]
        except Exception as e:
            return [f"Error: {str(e)}"]

    def setup_ui(self):
        """Configura la interfaz gráfica."""
        # Frame superior con dos columnas: Configuración e IPs
        top_frame = ttk.Frame(self.root, style="TFrame")
        top_frame.pack(fill="x", padx=10, pady=5)

        # Columna izquierda: Configuración
        config_frame = ttk.LabelFrame(top_frame, text="Configuración", style="Custom.TLabelframe")
        config_frame.pack(side="left", fill="both", expand=True, padx=5)

        # Campo para IP del receptor
        ttk.Label(config_frame, text="IP Receptor:", style="TLabel").pack(anchor="w", padx=5, pady=5)
        self.ip_entry = ttk.Entry(
            config_frame,
            textvariable=self.HOST_RECEPTOR,
            width=20,
            style="Dark.TEntry"
        )
        self.ip_entry.pack(fill="x", padx=5, pady=5)
        self.ip_entry.insert(0, "127.0.0.1")

        # Control de amplificación (con etiqueta de valor)
        amp_label_frame = ttk.Frame(config_frame, style="TFrame")
        amp_label_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(amp_label_frame, text="Amplificación:", style="TLabel").pack(side="left")
        self.amp_value_label = ttk.Label(amp_label_frame, text="1.0x", foreground="#ffaa00", style="TLabel", font=("Segoe UI", 10, "bold"))
        self.amp_value_label.pack(side="right")

        self.amplification_slider = ttk.Scale(
            config_frame,
            from_=1.0,
            to=5.0,
            variable=self.AMPLIFICATION_FACTOR,
            orient="horizontal",
            style="Horizontal.TScale",
            cursor="sb_h_double_arrow",
            command=self.update_amp_label
        )
        self.amplification_slider.pack(fill="x", padx=5, pady=5)
        # Inicializar etiqueta con valor actual
        self.update_amp_label(self.AMPLIFICATION_FACTOR.get())

        # Columna derecha: IPs locales
        ips_info_frame = ttk.LabelFrame(top_frame, text="IPs Locales Disponibles", style="Custom.TLabelframe")
        ips_info_frame.pack(side="left", fill="both", expand=True, padx=5)

        ips_list = self.get_local_ips()
        for ip in ips_list:
            ip_label = ttk.Label(
                ips_info_frame,
                text=f"  • {ip}",
                foreground=COLORS["fg_white"],
                style="TLabel"
            )
            ip_label.pack(anchor="w", padx=10, pady=2)

        # Frame de botones (ancho completo)
        button_frame = ttk.LabelFrame(self.root, text="Controles", style="Custom.TLabelframe")
        button_frame.pack(fill="x", padx=10, pady=5)

        self.start_button = ttk.Button(
            button_frame,
            text="Iniciar Transmisión",
            command=self.start_transmission,
            style="Primary.TButton"
        )
        self.start_button.pack(side="left", padx=5, pady=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="Detener Transmisión",
            command=self.stop_transmission,
            state=tk.DISABLED,
            style="Disabled.TButton"
        )
        self.stop_button.pack(side="left", padx=5, pady=5)

        # Gráfico de audio (ancho completo)
        graph_frame = ttk.LabelFrame(self.root, text="Señal de Audio", style="Custom.TLabelframe")
        graph_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.figure, self.ax, self.canvas, self.line, self.audio_buffer = create_plot(graph_frame, self.CHUNK)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        # Etiqueta de estado (ancho completo, más grande)
        status_frame = ttk.LabelFrame(self.root, text="Estado", style="Custom.TLabelframe")
        status_frame.pack(fill="x", padx=10, pady=5)

        self.status_label = ttk.Label(
            status_frame,
            text="Detenido",
            foreground=COLORS["status_red"],
            style="TLabel",
            font=("Segoe UI", 14, "bold")
        )
        self.status_label.pack(pady=10)

    def log_message(self, message):
        """Registra mensajes en consola."""
        print(message)

    def update_status(self, message, color="white"):
        """Actualiza etiqueta de estado de forma segura desde threads."""
        self.status_label.config(text=message, foreground=color)

    def update_plot(self):
        """Actualiza el gráfico con datos de audio."""
        self.line.set_ydata(self.audio_buffer)
        self.canvas.draw()
        if self.transmitting:
            self.root.after(50, self.update_plot)

    def update_amp_label(self, value):
        """Actualiza la etiqueta del valor de amplificación."""
        try:
            val = float(value)
        except Exception:
            return
        if val > 5.0:
            self.amp_value_label.config(text=f"{val:.1f}x ⚠️ MAX", foreground="#ff0000")
        elif abs(val - 5.0) < 1e-6:
            self.amp_value_label.config(text="5.0x MAX", foreground="#ffaa00")
        else:
            self.amp_value_label.config(text=f"{val:.1f}x", foreground="#00ff00")

    def start_transmission(self):
        """Inicia el proceso de transmisión."""
        host = self.HOST_RECEPTOR.get().strip()

        if not host:
            messagebox.showwarning("Advertencia", "Ingresa una IP de receptor válida.")
            return

        self.transmitting = True
        self.transmit_event.clear()
        self.start_button.config(state=tk.DISABLED, style="Disabled.TButton")
        self.stop_button.config(state=tk.NORMAL, style="Primary.TButton")
        self.log_message(f"Preparando transmisión a {host}:{self.PORT}...")

        threading.Thread(target=self.countdown_and_transmit, args=(host,), daemon=True).start()

    def countdown_and_transmit(self, host):
        """Cuenta regresiva antes de iniciar la transmisión."""
        self.root.after(0, self.update_status, "Preparando... Iniciando en 5 segundos...", COLORS["status_yellow"])

        for i in range(5, 0, -1):
            if self.transmit_event.is_set():
                self.root.after(0, self.update_status, "Detenido", COLORS["status_red"])
                return
            self.root.after(0, self.update_status, f"Preparando... Iniciando en {i} segundos...", COLORS["status_yellow"])
            time.sleep(1)

        if self.transmit_event.is_set():
            self.root.after(0, self.update_status, "Detenido", COLORS["status_red"])
            return

        self.root.after(0, self.update_status, "¡Transmisión iniciada!", COLORS["status_green"])
        self.run_transmission(host)

    def run_transmission(self, host):
        """Ejecuta el bucle principal de transmisión."""
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            self.update_plot()

            while not self.transmit_event.is_set():
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                processed_audio = np.clip(
                    audio_data * self.AMPLIFICATION_FACTOR.get(),
                    -32768, 32767
                ).astype(np.int16)
                self.audio_buffer = audio_data.copy()

                self.s.sendto(processed_audio.tobytes(), (host, self.PORT))

        except Exception as e:
            self.log_message(f"Error en transmisión: {e}")
        finally:
            self.root.after(0, self.stop_transmission)

    def stop_transmission(self):
        """Detiene la transmisión y libera recursos."""
        if not self.transmitting:
            return

        self.transmitting = False
        self.transmit_event.set()

        self.start_button.config(state=tk.NORMAL, style="Primary.TButton")
        self.stop_button.config(state=tk.DISABLED, style="Disabled.TButton")
        self.root.after(0, self.update_status, "Detenido", COLORS["status_red"])
        self.log_message("\nTransmisión detenida.")

        # Limpiar recursos
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        if self.p:
            try:
                self.p.terminate()
            except:
                pass
        if self.s:
            try:
                self.s.close()
            except:
                pass

    def on_close(self):
        """Maneja el cierre de la ventana."""
        self.stop_transmission()
        self.root.after(100, self.root.destroy)
        sys.exit(0)


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioTransmitterApp(root)
    root.mainloop()
