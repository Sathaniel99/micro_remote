"""
common.py - Módulo compartido para interfaces de audio UDP (emisor y receptor)

Proporciona:
- Configuración de audio (CHUNK, FORMAT, CHANNELS, RATE)
- Funciones para setup de estilos ttk
- Funciones para crear gráficos matplotlib
- Utilidades UI (centrar ventana, combobox oscuro, etc.)
"""

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from tkinter import ttk
import tkinter as tk
import numpy as np
import pyaudio

# ==================== CONFIGURACIÓN DE AUDIO ====================
AUDIO_CONFIG = {
    "CHUNK": 2048,
    "FORMAT": pyaudio.paInt16,
    "CHANNELS": 1,
    "RATE": 44100,
}

# ==================== COLORES Y ESTILOS ====================
COLORS = {
    "bg_main": "#0d0d1c",
    "bg_secondary": "#171726",
    "bg_dark": "#0f0f1b",
    "fg_white": "white",
    "fg_gray": "#888888",
    "border_light": "#1D1D31",
    "border_focus": "#1D1D31",
    "border_active": "#1D1D31",
    "button_active": "#14142c",
    "button_pressed": "#0c0c26",
    "button_disabled": "#2a2a3a",
    "select_bg": "#14142c",
    "select_fg": "white",
    "status_green": "green",
    "status_red": "red",
    "status_yellow": "#ffaa00",
}


def setup_style():
    """
    Configura los estilos ttk globales.
    Retorna la instancia de ttk.Style() configurada.
    """
    style = ttk.Style()
    style.theme_use('clam')

    # Fondo general
    style.configure("TFrame", background=COLORS["bg_main"])
    style.configure("TLabel", background=COLORS["bg_main"], foreground=COLORS["fg_white"])
    style.configure("Horizontal.TScale", 
                    background=COLORS["bg_main"], 
                    troughcolor=COLORS["bg_secondary"], 
                    foreground=COLORS["fg_white"])

    # Combobox oscuro
    style.configure("Dark.TCombobox",
                    fieldbackground=COLORS["bg_secondary"],
                    background=COLORS["bg_secondary"],
                    foreground=COLORS["fg_white"],
                    selectbackground=COLORS["select_bg"],
                    selectforeground=COLORS["select_fg"],
                    arrowcolor=COLORS["fg_white"],
                    bordercolor=COLORS["border_light"],
                    lightcolor=COLORS["border_light"],
                    darkcolor=COLORS["border_light"])
    style.map("Dark.TCombobox",
              fieldbackground=[("readonly", COLORS["bg_secondary"])],
              foreground=[("readonly", COLORS["fg_white"])])

    # Entry oscuro
    style.configure("Dark.TEntry",
                    fieldbackground=COLORS["bg_secondary"],
                    background=COLORS["bg_secondary"],
                    foreground=COLORS["fg_white"],
                    insertcolor=COLORS["fg_white"],
                    bordercolor=COLORS["border_light"],
                    lightcolor=COLORS["border_light"],
                    darkcolor=COLORS["border_light"])

    # Botón primario (activo)
    style.configure("Primary.TButton",
                    background=COLORS["bg_main"],
                    foreground=COLORS["fg_white"],
                    borderwidth=1,
                    relief="solid",
                    bordercolor=COLORS["border_focus"],
                    padding=(12, 6),
                    font=("Segoe UI", 10, "bold"))
    style.map("Primary.TButton",
              background=[("active", COLORS["button_active"]), ("pressed", COLORS["button_pressed"])],
              foreground=[("active", COLORS["fg_white"])],
              bordercolor=[("active", COLORS["border_active"])])

    # Botón deshabilitado
    style.configure("Disabled.TButton",
                    background=COLORS["button_disabled"],
                    foreground=COLORS["fg_gray"],
                    borderwidth=1,
                    relief="solid",
                    bordercolor=COLORS["border_light"],
                    padding=(12, 6),
                    font=("Segoe UI", 10, "bold"))

    # LabelFrame personalizado
    style.configure("Custom.TLabelframe",
                    background=COLORS["bg_main"],
                    relief="solid",
                    borderwidth=1,
                    bordercolor=COLORS["border_focus"])
    style.configure("Custom.TLabelframe.Label",
                    background=COLORS["bg_main"],
                    foreground=COLORS["fg_white"],
                    font=("Segoe UI", 9, "bold"))

    return style


def create_plot(root, chunk_size=1024):
    """
    Crea un gráfico matplotlib configurado para visualizar audio en tiempo real.

    Args:
        root: ventana tk.Tk o frame contenedor
        chunk_size: tamaño del buffer de audio (defecto: AUDIO_CONFIG["CHUNK"])

    Retorna:
        tuple: (figure, ax, canvas, line, buffer_array)
            - figure: objeto Figure de matplotlib
            - ax: objeto Axes
            - canvas: widget FigureCanvasTkAgg listo para empacar
            - line: Line2D object para actualizar datos
            - buffer_array: numpy array inicializado con ceros
    """
    buffer = np.zeros(chunk_size)
    fig, ax = plt.subplots(figsize=(6, 2), facecolor=COLORS["bg_dark"])
    ax.set_facecolor(COLORS["bg_dark"])
    
    line, = ax.plot(buffer, color=COLORS["fg_white"], lw=1)
    ax.set_ylim(-32768, 32767)
    ax.set_xlim(0, chunk_size)
    ax.tick_params(axis='x', colors=COLORS["fg_white"])
    ax.tick_params(axis='y', colors=COLORS["fg_white"])
    
    for spine in ax.spines.values():
        spine.set_color(COLORS["bg_secondary"])
    
    ax.set_title("Señal de Audio en Tiempo Real", color=COLORS["fg_white"], fontsize=10)
    
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().configure(
        bg=COLORS["bg_dark"],
        highlightthickness=1,
        highlightbackground=COLORS["bg_secondary"]
    )

    return fig, ax, canvas, line, buffer


def center_window(root, width=700, height=600):
    """
    Centra una ventana tk en la pantalla.

    Args:
        root: ventana tk.Tk
        width: ancho de la ventana (defecto: 700)
        height: alto de la ventana (defecto: 600)
    """
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int(screen_width / 2 - width / 2)
    y = int(screen_height / 2 - height / 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.resizable(False, False)


def configure_window(root, title, width=700, height=600, icon_name="app_icon.ico"):
    """
    Configura una ventana completa: título, geometría, fondo e icono.

    Args:
        root: ventana tk.Tk
        title: título de la ventana
        width: ancho (defecto: 700)
        height: alto (defecto: 600)
        icon_name: nombre del archivo icono en la carpeta 'icons' (defecto: "app_icon.ico")
    """
    import os
    import sys
    
    root.title(title)
    center_window(root, width, height)
    root.configure(bg=COLORS["bg_main"])
    
    # ========== CARGAR ICONO PARA TÍTULO DE VENTANA ==========
    # Construir lista de rutas donde buscar el icono
    icon_paths = []
    
    # Ruta 1: Carpeta del script (modo desarrollo)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_paths.append(os.path.join(script_dir, 'icons', icon_name))
    
    # Ruta 2: Si está empaquetado con PyInstaller (--add-data "icons;icons")
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        # PyInstaller coloca resources con --add-data relativo a sys._MEIPASS
        icon_paths.append(os.path.join(base_path, 'icons', icon_name))
        # Fallback: directamente en raíz
        icon_paths.append(os.path.join(base_path, icon_name))
    
    # Intentar cargar cada ruta hasta encontrar el icono
    for icon_path in icon_paths:
        normalized_path = os.path.normpath(icon_path)
        if os.path.exists(normalized_path) and os.path.isfile(normalized_path):
            try:
                root.iconbitmap(normalized_path)
                return  # Exitoso, salir
            except tk.TclError:
                # Archivo .ico corrupto o inválido, intentar siguiente
                continue
            except Exception:
                # Otro error, continuar
                continue
