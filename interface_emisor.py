"""
interface_emisor.py - Interfaz de transmisión de audio UDP con NetScanner mejorado

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
import subprocess
import ipaddress
import platform
from concurrent.futures import ThreadPoolExecutor
import os

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


class NetworkScanner:
    def __init__(self):
        self.active_ips = []
        self.scanning = False
        self.own_ips = self.get_own_ips()
        
    def get_own_ips(self):
        """Obtiene todas las IPs propias del dispositivo."""
        try:
            hostname = socket.gethostname()
            hostname_ex = socket.gethostbyname_ex(hostname)
            # El tercer elemento contiene las IPs
            own_ips = hostname_ex[2]
            print(f"IPs propias del dispositivo: {own_ips}")
            return own_ips
        except Exception as e:
            print(f"Error obteniendo IPs propias: {e}")
            return []
        
    def ping_ip_improved(self, ip):
        """Método mejorado de ping con diferentes estrategias."""
        # Excluir IPs que no queremos escanear
        if ip in ["127.0.0.1", "localhost"] or ip in self.own_ips:
            return False
            
        # Método 1: Ping tradicional
        try:
            if platform.system().lower() == "windows":
                result = subprocess.run(
                    ["ping", "-n", "1", "-w", "1000", str(ip)],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
            else:
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "1", str(ip)],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
            return result.returncode == 0
        except:
            pass
        
        # Método 2: Intentar conexión por socket en puertos comunes
        try:
            for port in [80, 443, 22, 21, 135, 139, 445]:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((str(ip), port))
                sock.close()
                if result == 0:
                    return True
        except:
            pass
        
        return False

    def get_local_subnets(self):
        """Obtiene las subredes locales basadas en las IPs de la máquina."""
        try:
            print(f"IPs propias para generar subredes: {self.own_ips}")
            
            subnets = []
            for ip in self.own_ips:
                try:
                    # Crear objeto IP y obtener la subred /24
                    ip_obj = ipaddress.IPv4Address(ip)
                    # Usar notación wildcard como solicitaste
                    base_parts = ip.split('.')
                    wildcard_subnet = f"{base_parts[0]}.{base_parts[1]}.{base_parts[2]}.*"
                    subnet_cidr = f"{base_parts[0]}.{base_parts[1]}.{base_parts[2]}.0/24"
                    
                    if wildcard_subnet not in subnets:
                        subnets.append(wildcard_subnet)
                        print(f"Subred encontrada: {wildcard_subnet} (desde IP: {ip})")
                        
                except Exception as e:
                    print(f"Error procesando IP {ip}: {e}")
                    continue
            
            # Si no encontramos subredes, usar algunas comunes
            if not subnets:
                common_subnets = [
                    "192.168.1.*",
                    "192.168.0.*", 
                    "10.0.0.*"
                ]
                subnets.extend(common_subnets)
                print(f"Usando subredes por defecto: {common_subnets}")
            
            return subnets
            
        except Exception as e:
            print(f"Error obteniendo subredes locales: {e}")
            return ["192.168.1.*", "192.168.0.*"]  # Subredes por defecto

    def wildcard_to_cidr(self, wildcard_subnet):
        """Convierte notación wildcard (192.168.1.*) a CIDR (192.168.1.0/24)."""
        try:
            base_ip = wildcard_subnet.replace('*', '0')
            return f"{base_ip}/24"
        except:
            return wildcard_subnet

    def scan_subnet_optimized(self, wildcard_subnet):
        """Escanea una subred de forma optimizada usando notación wildcard."""
        try:
            # Convertir wildcard a CIDR para el escaneo
            cidr_subnet = self.wildcard_to_cidr(wildcard_subnet)
            network = ipaddress.IPv4Network(cidr_subnet, strict=False)
            
            # Escanear solo un rango más pequeño para mayor velocidad
            base_ip = str(network.network_address).split('.')
            ips_to_scan = []
            
            # Escanear del 1 al 254 (excluyendo .0 y .255)
            for i in range(1, 255):
                ip = f"{base_ip[0]}.{base_ip[1]}.{base_ip[2]}.{i}"
                # Excluir IPs propias del dispositivo
                if ip not in self.own_ips:
                    ips_to_scan.append(ip)
            
            print(f"Escaneando {len(ips_to_scan)} IPs en {wildcard_subnet}...")
            
            active_ips = []
            with ThreadPoolExecutor(max_workers=15) as executor:
                results = list(executor.map(self.ping_ip_improved, ips_to_scan))
                active_ips = [ip for ip, active in zip(ips_to_scan, results) if active]
            
            print(f"Subred {wildcard_subnet}: {len(active_ips)} IPs activas encontradas")
            return active_ips
            
        except Exception as e:
            print(f"Error escaneando subred {wildcard_subnet}: {e}")
            return []

    def scan_network(self):
        """Escanea todas las subredes locales."""
        self.scanning = True
        self.active_ips = []
        
        try:
            # Obtener subredes locales
            subnets = self.get_local_subnets()
            print(f"Subredes a escanear: {subnets}")
            
            # Escanear cada subred
            all_active_ips = []
            for subnet in subnets:
                active_ips = self.scan_subnet_optimized(subnet)
                all_active_ips.extend(active_ips)
            
            # Filtrar IPs no deseadas
            filtered_ips = []
            for ip in all_active_ips:
                if (ip not in ["127.0.0.1", "localhost"] and 
                    ip not in self.own_ips):
                    filtered_ips.append(ip)
            
            self.active_ips = list(set(filtered_ips))  # Remover duplicados
            print(f"IPs filtradas finales: {self.active_ips}")
            return self.active_ips
            
        except Exception as e:
            print(f"Error en escaneo general: {e}")
            return []
        finally:
            self.scanning = False


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

        # NetScanner
        self.scanner = NetworkScanner()
        self.scanning = False

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
        """Configura la interfaz gráfica según el diseño exacto de la imagen."""
        # Frame principal
        main_frame = ttk.Frame(self.root, style="TFrame")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ========== FILA 1: CONFIGURACIÓN E IPs LOCALES ==========
        row1_frame = ttk.Frame(main_frame, style="TFrame")
        row1_frame.pack(fill="x", pady=(0, 10))
        
        # --- CONFIGURACIÓN (Izquierda) ---
        config_frame = ttk.LabelFrame(row1_frame, text="Configuración", style="Custom.TLabelframe")
        config_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # IP Receptor
        ttk.Label(config_frame, text="IP Receptor", style="TLabel").pack(anchor="w", padx=10, pady=(10, 2))
        
        ip_entry_frame = ttk.Frame(config_frame, style="TFrame")
        ip_entry_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.ip_entry = ttk.Entry(
            ip_entry_frame,
            textvariable=self.HOST_RECEPTOR,
            width=20,
            style="Dark.TEntry"
        )
        self.ip_entry.pack(side="left", fill="x", expand=True)
        self.ip_entry.insert(0, "127.0.0.1")
        
        # Botón de escaneo de red
        self.scan_button = ttk.Button(
            ip_entry_frame,
            text="Escanear Red",
            command=self.start_network_scan,
            style="Primary.TButton",
            width=12
        )
        self.scan_button.pack(side="right", padx=(5, 0))
        
        # Información de escaneo
        scan_info_frame = ttk.Frame(config_frame, style="TFrame")
        scan_info_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.scan_info_label = ttk.Label(
            scan_info_frame,
            text="Escanea IPs en subredes locales",
            foreground=COLORS["fg_gray"],
            style="TLabel",
            font=("Segoe UI", 8)
        )
        self.scan_info_label.pack(anchor="w")
        
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
        
        # --- IPs LOCALES (Derecha) ---
        ips_frame = ttk.LabelFrame(row1_frame, text="IPs Locales y de Red", style="Custom.TLabelframe")
        ips_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Frame para lista de IPs con scrollbar
        ip_list_frame = ttk.Frame(ips_frame, style="TFrame")
        ip_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Crear Text widget para mostrar IPs (solo lectura)
        self.ip_text = tk.Text(
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
        
        scrollbar = ttk.Scrollbar(ip_list_frame, orient="vertical", command=self.ip_text.yview)
        self.ip_text.configure(yscrollcommand=scrollbar.set)
        
        # Insertar IPs locales iniciales
        self.update_ip_list()
        
        self.ip_text.pack(side="left", fill="both", expand=True)
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
            text="Iniciar Transmisión",
            command=self.start_transmission,
            style="Primary.TButton",
            width=18
        )
        self.start_button.pack(side="left", padx=(0, 10))
        
        self.stop_button = ttk.Button(
            button_center_frame,
            text="Detener Transmisión",
            command=self.stop_transmission,
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
        
        # Inicializar etiqueta de amplificación
        self.update_amp_label(self.AMPLIFICATION_FACTOR.get())

    def update_ip_list(self, scanned_ips=None, subnets_info=None):
        """Actualiza la lista de IPs en el widget de texto."""
        self.ip_text.config(state="normal")
        self.ip_text.delete(1.0, tk.END)
        
        if scanned_ips is not None:
            # Mostrar IPs escaneadas
            if scanned_ips:
                self.ip_text.insert(tk.END, "=== IPs Encontradas en Red ===\n\n")
                for ip in scanned_ips:
                    self.ip_text.insert(tk.END, f"  • {ip}\n")
                
                if subnets_info:
                    self.ip_text.insert(tk.END, f"\nSubredes escaneadas:\n")
                    for subnet in subnets_info:
                        self.ip_text.insert(tk.END, f"  • {subnet}\n")
            else:
                self.ip_text.insert(tk.END, "=== No se encontraron IPs ===\n\n")
                self.ip_text.insert(tk.END, "Solo se muestran IPs externas\n")
                self.ip_text.insert(tk.END, "(excluyendo IP propia y localhost)")
        else:
            # Mostrar IPs locales por defecto
            ips_list = self.get_local_ips()
            self.ip_text.insert(tk.END, "=== IPs Locales ===\n\n")
            for ip in ips_list:
                self.ip_text.insert(tk.END, f"  • {ip}\n")
            
            self.ip_text.insert(tk.END, f"\nPresione 'Escanear Red' para\n")
            self.ip_text.insert(tk.END, f"buscar dispositivos externos")
        
        self.ip_text.config(state="disabled")

    def start_network_scan(self):
        """Inicia el escaneo de red en un hilo separado."""
        if self.scanning:
            return
            
        self.scanning = True
        self.scan_button.config(state=tk.DISABLED, style="Disabled.TButton")
        self.update_status("Obteniendo subredes...", COLORS["status_yellow"])
        
        # Ejecutar escaneo en hilo separado
        threading.Thread(target=self.run_network_scan, daemon=True).start()

    def run_network_scan(self):
        """Ejecuta el escaneo de red."""
        try:
            self.log_message("Iniciando escaneo de subredes locales...")
            
            # Obtener información de subredes primero
            subnets = self.scanner.get_local_subnets()
            self.root.after(0, self.update_status, f"Escaneando {len(subnets)} subredes...", COLORS["status_yellow"])
            
            # Realizar escaneo
            active_ips = self.scanner.scan_network()
            
            # Actualizar UI en el hilo principal
            self.root.after(0, self.on_scan_complete, active_ips, subnets)
            
        except Exception as e:
            self.root.after(0, self.on_scan_error, str(e))

    def on_scan_complete(self, active_ips, subnets):
        """Se ejecuta cuando el escaneo se completa."""
        self.scanning = False
        self.scan_button.config(state=tk.NORMAL, style="Primary.TButton")
        
        if active_ips:
            self.update_status(f"Escaneo: {len(active_ips)} IPs externas", COLORS["status_green"])
            self.update_ip_list(active_ips, subnets)
            self.log_message(f"Escaneo completado. {len(active_ips)} IPs externas encontradas en {len(subnets)} subredes.")
            
            # Si hay IPs encontradas, sugerir la primera
            if active_ips and not self.HOST_RECEPTOR.get().strip():
                self.HOST_RECEPTOR.set(active_ips[0])
        else:
            self.update_status("Escaneo: 0 IPs externas", COLORS["status_red"])
            self.update_ip_list([], subnets)
            self.log_message("Escaneo completado. No se encontraron IPs externas.")

    def on_scan_error(self, error_message):
        """Se ejecuta cuando ocurre un error en el escaneo."""
        self.scanning = False
        self.scan_button.config(state=tk.NORMAL, style="Primary.TButton")
        self.update_status("Error en escaneo", COLORS["status_red"])
        self.update_ip_list()  # Volver a mostrar IPs locales
        messagebox.showerror("Error", f"Error en escaneo de red:\n{error_message}")
        self.log_message(f"Error en escaneo: {error_message}")

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

    def log_message(self, message):
        """Registra mensajes en consola."""
        print(message)

    def update_status(self, message, color="white"):
        """Actualiza etiqueta de estado de forma segura desde threads."""
        self.status_label.config(text=message, foreground=color)
        self.update_status_background(color)

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
        self.root.after(0, self.update_status, "Iniciando en 5 segundos...", COLORS["status_yellow"])

        for i in range(5, 0, -1):
            if self.transmit_event.is_set():
                self.root.after(0, self.update_status, "Detenido", COLORS["status_red"])
                return
            self.root.after(0, self.update_status, f"Iniciando en {i} segundos...", COLORS["status_yellow"])
            time.sleep(1)

        if self.transmit_event.is_set():
            self.root.after(0, self.update_status, "Detenido", COLORS["status_red"])
            return

        self.root.after(0, self.update_status, "¡Transmisión iniciada!", COLORS["status_green"])
        self.run_transmission(host)

    def run_transmission(self, host):
        """Ejecuta el bucle principal de transmisión."""
        try:
            # Crear nuevos recursos para esta sesión
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
                try:
                    data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    processed_audio = np.clip(
                        audio_data * self.AMPLIFICATION_FACTOR.get(),
                        -32768, 32767
                    ).astype(np.int16)
                    self.audio_buffer = audio_data.copy()

                    # Verificar que el socket aún es válido antes de enviar
                    if self.s and not self.transmit_event.is_set():
                        self.s.sendto(processed_audio.tobytes(), (host, self.PORT))
                    
                except socket.error as e:
                    if not self.transmit_event.is_set():
                        self.log_message(f"Error de socket durante transmisión: {e}")
                    break
                except Exception as e:
                    if not self.transmit_event.is_set():
                        self.log_message(f"Error durante transmisión: {e}")
                    break

        except Exception as e:
            if not self.transmit_event.is_set():
                self.log_message(f"Error al iniciar transmisión: {e}")
        finally:
            # Solo llamar stop_transmission si no fue ya llamado
            if not self.transmit_event.is_set():
                self.root.after(0, self.cleanup_resources)

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
        self.transmitting = False
        self.start_button.config(state=tk.NORMAL, style="Primary.TButton")
        self.stop_button.config(state=tk.DISABLED, style="Disabled.TButton")
        self.update_status("Detenido", COLORS["status_red"])
        self.log_message("Transmisión detenida.")

    def stop_transmission(self):
        """Detiene la transmisión de forma segura."""
        if not self.transmitting:
            return

        self.transmit_event.set()
        self.log_message("Solicitando detención de transmisión...")

        # Iniciar limpieza en un hilo separado para no bloquear la UI
        threading.Thread(target=self.cleanup_resources, daemon=True).start()

    def on_close(self):
        """Maneja el cierre de la ventana."""
        self.stop_transmission()
        self.root.after(100, self.root.destroy)
        sys.exit(0)


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioTransmitterApp(root)
    root.mainloop()