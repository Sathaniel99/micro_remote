"""
interface_receptor.py - Interfaz de recepción de audio UDP

Requiere:
- pyaudio: reproducción de audio en altavoces
- common.py: estilos compartidos y utilidades UI
"""

from tkinter import ttk
import tkinter as tk
import numpy as np
import threading
import pyaudio
import socket
import sys

from common import ( AUDIO_CONFIG, COLORS, setup_style, create_plot, configure_window )


class AudioReceiverApp:
    def __init__(self, root):
        self.root = root
        
        # Configurar ventana base
        configure_window(self.root, "Receptor de Audio UDP", icon_name="receptor.ico")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Configuración de audio
        self.CHUNK = AUDIO_CONFIG["CHUNK"]
        self.FORMAT = AUDIO_CONFIG["FORMAT"]
        self.CHANNELS = AUDIO_CONFIG["CHANNELS"]
        self.RATE = AUDIO_CONFIG["RATE"]

        # Configuración de red
        self.HOST = '0.0.0.0'
        self.PORT = 5000

        # Variables de control
        self.AMPLIFICATION_FACTOR = tk.DoubleVar(value=1.0)
        self.VOLUME_FACTOR = tk.DoubleVar(value=1.0)
        
        # Estado
        self.receiving = False
        self.p = None
        self.stream = None
        self.s = None
        self.reception_thread = None
        self.update_plot_id = None

        # Buffer para gráfico
        self.audio_buffer = np.zeros(self.CHUNK)

        # Setup UI con estilos compartidos
        setup_style()
        self.setup_ui()

    def on_close(self):
        """Se ejecuta al cerrar la ventana."""
        self.stop_reception()
        sys.exit(0)

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

        # Control de volumen (con etiqueta de valor)
        vol_label_frame = ttk.Frame(config_frame, style="TFrame")
        vol_label_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(vol_label_frame, text="Volumen:", style="TLabel").pack(side="left")
        self.vol_value_label = ttk.Label(vol_label_frame, text="1.0x", foreground="#ffaa00", style="TLabel", font=("Segoe UI", 10, "bold"))
        self.vol_value_label.pack(side="right")

        self.volume_slider = ttk.Scale(
            config_frame,
            from_=0.0,
            to=2.0,
            variable=self.VOLUME_FACTOR,
            orient="horizontal",
            style="Horizontal.TScale",
            cursor="sb_h_double_arrow",
            command=self.update_vol_label
        )
        self.volume_slider.pack(fill="x", padx=5, pady=5)
        # Inicializar etiqueta con valor actual
        self.update_vol_label(self.VOLUME_FACTOR.get())

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
            text="Iniciar Recepción",
            command=self.start_reception,
            style="Primary.TButton"
        )
        self.start_button.pack(side="left", padx=5, pady=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="Detener Recepción",
            command=self.stop_reception,
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

    def update_plot(self):
        """Actualiza el gráfico con datos de audio."""
        try:
            self.line.set_ydata(self.audio_buffer)
            self.canvas.draw()
        except Exception:
            pass
        if self.receiving:
            self.update_plot_id = self.root.after(50, self.update_plot)

    def update_amp_label(self, value):
        """Actualiza la etiqueta del valor de amplificación."""
        try:
            val = float(value)
        except Exception:
            return
        # Señales visuales para máximo/sobrepaso
        if val > 5.0:
            self.amp_value_label.config(text=f"{val:.1f}x ⚠️ MAX", foreground="#ff0000")
        elif abs(val - 5.0) < 1e-6:
            self.amp_value_label.config(text="5.0x MAX", foreground="#ffaa00")
        else:
            self.amp_value_label.config(text=f"{val:.1f}x", foreground="#00ff00")

    def update_vol_label(self, value):
        """Actualiza la etiqueta del valor de volumen."""
        try:
            val = float(value)
        except Exception:
            return
        if val > 2.0:
            self.vol_value_label.config(text=f"{val:.1f}x ⚠️ MAX", foreground="#ff0000")
        elif abs(val - 2.0) < 1e-6:
            self.vol_value_label.config(text="2.0x MAX", foreground="#ffaa00")
        elif abs(val - 0.0) < 1e-6:
            self.vol_value_label.config(text="0.0x MIN", foreground="#0099ff")
        else:
            self.vol_value_label.config(text=f"{val:.1f}x", foreground="#00ff00")

    def start_reception(self):
        """Inicia la recepción de audio."""
        if self.receiving:
            return

        self.receiving = True
        self.start_button.config(state=tk.DISABLED, style="Disabled.TButton")
        self.stop_button.config(state=tk.NORMAL, style="Primary.TButton")
        self.status_label.config(text="Estado: Escuchando...", foreground=COLORS["status_green"])

        self.reception_thread = threading.Thread(target=self.run_reception, daemon=True)
        self.reception_thread.start()

        self.update_plot()

    def run_reception(self):
        """Ejecuta el bucle principal de recepción."""
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                output=True,
                frames_per_buffer=self.CHUNK
            )
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.s.bind((self.HOST, self.PORT))

            while self.receiving:
                try:
                    data, _ = self.s.recvfrom(self.CHUNK * 2 + 100)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    processed_audio = np.clip(
                        audio_data * self.AMPLIFICATION_FACTOR.get() * self.VOLUME_FACTOR.get(),
                        -32768, 32767
                    ).astype(np.int16)
                    self.stream.write(processed_audio.tobytes())
                    # Actualizar buffer para gráfico
                    try:
                        self.audio_buffer = audio_data[:self.CHUNK].copy() if len(audio_data) >= self.CHUNK else np.pad(audio_data, (0, self.CHUNK - len(audio_data)))
                    except Exception:
                        pass
                except socket.error:
                    break
        except Exception as e:
            self.log_message(f"Error en recepción: {e}")
        finally:
            self.stop_reception()

    def stop_reception(self):
        """Detiene la recepción y libera recursos."""
        if not self.receiving:
            return

        self.receiving = False

        # Cancelar actualización del gráfico
        if self.update_plot_id:
            self.root.after_cancel(self.update_plot_id)
            self.update_plot_id = None

        # Cambiar estado de botones
        self.start_button.config(state=tk.NORMAL, style="Primary.TButton")
        self.stop_button.config(state=tk.DISABLED, style="Disabled.TButton")
        self.status_label.config(text="Estado: Detenido", foreground=COLORS["status_red"])

        # Cerrar stream de audio
        if hasattr(self, 'stream') and self.stream:
            if self.stream.is_active():
                self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'p') and self.p:
            self.p.terminate()

        # Cerrar socket
        if hasattr(self, 's') and self.s:
            self.s.close()

    def log_message(self, message):
        """Registra mensajes en consola."""
        print(message)


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioReceiverApp(root)
    root.mainloop()
