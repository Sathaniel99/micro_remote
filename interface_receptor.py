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
        """Configura la interfaz gráfica según el diseño del emisor."""
        # Frame principal
        main_frame = ttk.Frame(self.root, style="TFrame")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ========== FILA 1: CONFIGURACIÓN E IPs LOCALES ==========
        row1_frame = ttk.Frame(main_frame, style="TFrame")
        row1_frame.pack(fill="x", pady=(0, 10))
        
        # --- CONFIGURACIÓN (Izquierda) ---
        config_frame = ttk.LabelFrame(row1_frame, text="Configuración", style="Custom.TLabelframe")
        config_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Amplificación
        ttk.Label(config_frame, text="Amplificación", style="TLabel").pack(anchor="w", padx=10, pady=(10, 2))
        
        amp_value_frame = ttk.Frame(config_frame, style="TFrame")
        amp_value_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.amp_value_label = ttk.Label(
            amp_value_frame, 
            text="1.0x", 
            foreground="#ffaa00", 
            style="TLabel", 
            font=("Segoe UI", 10, "bold")
        )
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
        self.amplification_slider.pack(fill="x", padx=10, pady=(0, 10))
        
        # Volumen
        ttk.Label(config_frame, text="Volumen", style="TLabel").pack(anchor="w", padx=10, pady=(0, 2))
        
        vol_value_frame = ttk.Frame(config_frame, style="TFrame")
        vol_value_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.vol_value_label = ttk.Label(
            vol_value_frame, 
            text="1.0x", 
            foreground="#ffaa00", 
            style="TLabel", 
            font=("Segoe UI", 10, "bold")
        )
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
        self.volume_slider.pack(fill="x", padx=10, pady=(0, 10))
        
        # --- IPs LOCALES (Derecha) ---
        ips_frame = ttk.LabelFrame(row1_frame, text="IPs Locales Disponibles", style="Custom.TLabelframe")
        ips_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Frame para lista de IPs con scrollbar
        ip_list_frame = ttk.Frame(ips_frame, style="TFrame")
        ip_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Crear Text widget para mostrar IPs (solo lectura)
        ip_text = tk.Text(
            ip_list_frame,
            height=4,
            width=25,
            bg=COLORS["bg_secondary"],
            fg=COLORS["fg_white"],
            font=("Consolas", 9),
            relief="flat",
            borderwidth=0,
            wrap="word",
            state="disabled"
        )
        
        scrollbar = ttk.Scrollbar(ip_list_frame, orient="vertical", command=ip_text.yview)
        ip_text.configure(yscrollcommand=scrollbar.set)
        
        # Insertar IPs en el texto
        ip_text.config(state="normal")
        ips_list = self.get_local_ips()
        for ip in ips_list:
            ip_text.insert("end", f"  • {ip}\n")
        ip_text.config(state="disabled")
        
        ip_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ========== FILA 2: CONTROLES Y ESTADO ==========
        row2_frame = ttk.Frame(main_frame, style="TFrame")
        row2_frame.pack(fill="x", pady=(0, 10))
        
        # --- CONTROLES (Izquierda - Se expande) ---
        controls_frame = ttk.LabelFrame(row2_frame, text="Controles", style="Custom.TLabelframe")
        controls_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Frame para los botones - CENTRADO
        button_container = ttk.Frame(controls_frame, style="TFrame")
        button_container.pack(expand=True, fill="both", padx=10, pady=15)
        
        # Frame interno para centrar los botones horizontalmente
        button_center_frame = ttk.Frame(button_container, style="TFrame")
        button_center_frame.pack(expand=True)
        
        self.start_button = ttk.Button(
            button_center_frame,
            text="Iniciar Recepción",
            command=self.start_reception,
            style="Primary.TButton",
            width=18
        )
        self.start_button.pack(side="left", padx=(0, 10))
        
        self.stop_button = ttk.Button(
            button_center_frame,
            text="Detener Recepción",
            command=self.stop_reception,
            state=tk.DISABLED,
            style="Disabled.TButton",
            width=18
        )
        self.stop_button.pack(side="left")
        
        # --- ESTADO (Derecha - Tamaño fijo) ---
        # Usar Frame normal en lugar de LabelFrame para poder cambiar el fondo
        self.status_container = tk.Frame(
            row2_frame,
            bg=COLORS["bg_secondary"],
            relief="solid",
            borderwidth=1,
            width=250,  # Ancho fijo
            height=80   # Alto fijo
        )
        self.status_container.pack(side="right", padx=(5, 0))
        self.status_container.pack_propagate(False)  # Evitar que se redimensione con el contenido
        
        # Título del frame de estado
        status_title = tk.Label(
            self.status_container,
            text="Estado",
            bg=COLORS["bg_main"],
            fg=COLORS["fg_white"],
            font=("Segoe UI", 9, "bold"),
            relief="solid",
            borderwidth=1
        )
        status_title.pack(fill="x", padx=1, pady=(1, 0))
        
        # Contenedor interno para el estado
        status_inner_frame = tk.Frame(self.status_container, bg=COLORS["bg_secondary"])
        status_inner_frame.pack(fill="both", expand=True, padx=1, pady=(0, 1))
        
        self.status_label = tk.Label(
            status_inner_frame,
            text="Iniciar",
            bg=COLORS["bg_secondary"],
            fg=COLORS["select_fg"],
            font=("Segoe UI", 14, "bold"),
            pady=20
        )
        self.status_label.pack(expand=True, fill="both")
        
        # ========== FILA 3: SEÑAL DE AUDIO (Ancho completo) ==========
        graph_frame = ttk.LabelFrame(main_frame, text="Señal de Audio", style="Custom.TLabelframe")
        graph_frame.pack(fill="both", expand=True)
        
        self.figure, self.ax, self.canvas, self.line, self.audio_buffer = create_plot(graph_frame, self.CHUNK)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # Inicializar etiquetas
        self.update_amp_label(self.AMPLIFICATION_FACTOR.get())
        self.update_vol_label(self.VOLUME_FACTOR.get())

    def update_status_background(self, color):
        """Actualiza el color de fondo del contenedor de estado según el color del texto."""
        color_map = {
            COLORS["status_red"]: "#1F0606",      # Rojo oscuro
            COLORS["status_green"]: "#081A08",    # Verde oscuro  
            COLORS["status_yellow"]: "#25250C",   # Amarillo oscuro
            "white": COLORS["bg_secondary"]       # Color por defecto
        }
        
        bg_color = color_map.get(color, COLORS["bg_secondary"])
        
        # Actualizar color de fondo del contenedor interno
        self.status_container.configure(bg=bg_color)
        self.status_label.master.configure(bg=bg_color)  # status_inner_frame
        self.status_label.configure(bg=bg_color)

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
        self.update_status("Escuchando...", COLORS["status_green"])

        self.reception_thread = threading.Thread(target=self.run_reception, daemon=True)
        self.reception_thread.start()

        self.update_plot()

    def update_status(self, message, color="white"):
        """Actualiza etiqueta de estado de forma segura."""
        self.status_label.config(text=message, foreground=color)
        self.update_status_background(color)

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
            self.s.settimeout(1.0)  # Timeout para poder verificar self.receiving
            self.s.bind((self.HOST, self.PORT))

            while self.receiving:
                try:
                    data, _ = self.s.recvfrom(self.CHUNK * 2 + 100)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    
                    # Aplicar procesamiento de audio
                    processed_audio = np.clip(
                        audio_data * self.AMPLIFICATION_FACTOR.get() * self.VOLUME_FACTOR.get(),
                        -32768, 32767
                    ).astype(np.int16)
                    
                    # Reproducir audio
                    self.stream.write(processed_audio.tobytes())
                    
                    # Actualizar buffer para gráfico
                    try:
                        if len(audio_data) >= self.CHUNK:
                            self.audio_buffer = audio_data[:self.CHUNK].copy()
                        else:
                            self.audio_buffer = np.pad(audio_data, (0, self.CHUNK - len(audio_data)))
                    except Exception:
                        pass
                        
                except socket.timeout:
                    # Timeout normal, continuar si aún estamos recibiendo
                    continue
                except socket.error:
                    # Error de socket, salir del bucle
                    break
                    
        except Exception as e:
            self.log_message(f"Error en recepción: {e}")
        finally:
            self.cleanup_resources()

    def cleanup_resources(self):
        """Limpia los recursos de audio y red de forma segura."""
        # Cerrar stream de audio
        if self.stream:
            try:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            except Exception as e:
                self.log_message(f"Error cerrando stream: {e}")

        # Terminar PyAudio
        if self.p:
            try:
                self.p.terminate()
                self.p = None
            except Exception as e:
                self.log_message(f"Error terminando PyAudio: {e}")

        # Cerrar socket
        if self.s:
            try:
                self.s.close()
                self.s = None
            except Exception as e:
                self.log_message(f"Error cerrando socket: {e}")

        # Actualizar estado en la interfaz
        self.root.after(0, self.finalize_stop)

    def finalize_stop(self):
        """Finaliza el estado de detención en la interfaz."""
        self.receiving = False
        self.start_button.config(state=tk.NORMAL, style="Primary.TButton")
        self.stop_button.config(state=tk.DISABLED, style="Disabled.TButton")
        self.update_status("Detenido", COLORS["status_red"])
        
        # Cancelar actualización del gráfico
        if self.update_plot_id:
            self.root.after_cancel(self.update_plot_id)
            self.update_plot_id = None
            
        self.log_message("Recepción detenida.")

    def stop_reception(self):
        """Detiene la recepción inmediatamente."""
        if not self.receiving:
            return

        self.receiving = False
        self.cleanup_resources()

    def log_message(self, message):
        """Registra mensajes en consola."""
        print(message)


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioReceiverApp(root)
    root.mainloop()