# micro_remoto

Aplicación simple de streaming de audio por UDP con interfaces gráficas (Tkinter) para Emisor y Receptor.

Resumen
- `interface_emisor.py`: GUI para capturar audio del micrófono y transmitir por UDP.
- `interface_receptor.py`: GUI para recibir audio por UDP y reproducirlo.
- `common.py`: configuración compartida (colores, estilos ttk, utilidades UI, creación de gráficos, carga de iconos).
- `convert_to_ico.py`: script para generar archivos `.ico` a partir de `.jpeg/.jpg` (genera un `.ico` por imagen en `icons/ico/`, resolución 256×256).
- `utils.py`: utilidades adicionales (p. ej. mapeo IPs).
- `requirements.txt`: dependencias del proyecto.
- `icons/`: contiene imágenes e iconos usados por la UI.

Objetivo

Aplicación para transmitir audio desde un emisor hacia uno o varios receptores en la red local, con controles de amplificación/volumen y visualización en tiempo real de la señal.

Requisitos

- Windows (desarrollado y probado en Windows)
- Python 3.11+ (en este repositorio hay una `venv/` preparada)
- Dependencias listadas en `requirements.txt` (PyAudio, NumPy, Matplotlib, Pillow, PyInstaller, etc.)

Instalación (entorno de desarrollo)

1. Activar el entorno virtual (si usas la `venv` incluida):

```powershell
# Desde PowerShell
C:\Users\Sathaniel\Desktop\PROGRAMACION\PROYECTOS\micro_remoto\venv\Scripts\Activate.ps1
```

2. O crear uno nuevo y instalar dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Ejecución en desarrollo

- Para ejecutar sin consola (y que el icono de la app pueda mostrarse correctamente en la barra de tareas durante desarrollo) usa `pythonw.exe`:

```powershell
C:\path\to\pythonw.exe interface_emisor.py
C:\path\to\pythonw.exe interface_receptor.py
```

- Si ejecutas con `python.exe` verás el icono de Python en la barra de tareas porque el proceso es el intérprete.

Generar iconos (.ico)

Si quieres generar iconos desde imágenes JPEG/JPG colocadas en `icons/`, usa el script `convert_to_ico.py`.

```powershell
# Ejecutar desde la raíz del proyecto (usa el python del venv si corresponde)
./python.exe convert_to_ico.py
```

Salida: `icons/ico/` contendrá un archivo `nombre.ico` (256×256) por cada imagen encontrada (`*.jpeg`, `*.jpg`).

Atención: el .ico generado por el script es multi-res (incluye 256×256) y está pensado para usarlo tanto en la ventana Tkinter como para el `--icon` de PyInstaller.

Empaquetado con PyInstaller

Ejemplos para crear ejecutables sin consola (`--windowed`) y con la carpeta `icons/` incluida en el bundle (importante para que `common.configure_window()` encuentre los iconos cuando el EXE se ejecuta):

```powershell
pyinstaller --onefile --windowed --icon=icons\ico\emisor.ico --add-data "icons;icons" --name emisor interface_emisor.py
pyinstaller --onefile --windowed --icon=icons\ico\receptor.ico --add-data "icons;icons" --name receptor interface_receptor.py
```

Notas importantes sobre iconos y PyInstaller

- `--icon` define el icono del archivo `.exe` (explorador de Windows).
- Tkinter necesita que llames a `root.iconbitmap(path)` para mostrar el icono en la barra de título / Alt+Tab / barra de tareas.
- `common.configure_window(root, title, icon_name="...")` busca el icono en:
  - `./icons/<icon_name>` (modo desarrollo)
  - dentro del bundle PyInstaller en `sys._MEIPASS` (cuando `getattr(sys, 'frozen', False)` es True)
- Por eso es importante usar `--add-data "icons;icons"` con PyInstaller para incluir la carpeta `icons`.

 # micro_remoto

 **micro_remoto** es una pequeña herramienta de streaming de audio por UDP con dos interfaces gráficas (Tkinter): un *emisor* que captura audio del micrófono y lo envía por la red, y un *receptor* que lo recibe y lo reproduce.

 ---

 ## Contenido principal

 - `interface_emisor.py` — Interfaz gráfica del emisor (captura y transmisión UDP).
 - `interface_receptor.py` — Interfaz gráfica del receptor (recepción y reproducción UDP).
 - `common.py` — Funciones y configuración compartida: estilos, colores, creación de gráficos, carga de iconos y utilidades UI.
 - `convert_to_ico.py` — Script para generar iconos `.ico` (256×256) a partir de imágenes JPG/JPEG.
 - `icons/` — Carpeta con imágenes y iconos; `icons/ico/` almacena los `.ico` generados.
 - `requirements.txt` — Dependencias del proyecto.

 ---

 ## Objetivo

 Transmitir audio desde un emisor hacia uno o varios receptores en la red local con controles de amplificación/volumen y visualización en tiempo real de la señal.

 ---

 ## Requisitos

 - Windows (desarrollado y probado en Windows).
 - Python 3.11+ (en el repositorio hay una `venv/` preparada).
 - Dependencias listadas en `requirements.txt` (PyAudio, NumPy, Matplotlib, Pillow, PyInstaller, etc.).

 ---

 ## Instalación (entorno de desarrollo)

 1. Activar el entorno virtual (si usas la `venv` incluida):

 ```powershell
 # Desde PowerShell (ajusta la ruta si no usas la `venv` incluida)
 C:\Users\Sathaniel\Desktop\PROGRAMACION\PROYECTOS\micro_remoto\venv\Scripts\Activate.ps1
 ```

 2. O crear uno nuevo e instalar dependencias:

 ```powershell
 python -m venv .venv
 .\.venv\Scripts\Activate.ps1
 python -m pip install -r requirements.txt
 ```

 ---

 ## Ejecución en desarrollo

 - Ejecutar sin consola (para que el icono de la app se muestre correctamente en la barra de tareas durante desarrollo):

 ```powershell
 C:\path\to\pythonw.exe interface_emisor.py
 C:\path\to\pythonw.exe interface_receptor.py
 ```

 - Si ejecutas con `python.exe` verás el icono del intérprete (Python) en la barra de tareas.

 ---

 ## Generar iconos (.ico)

 El script `convert_to_ico.py` busca imágenes `.jpeg`/`.jpg` en `icons/` y genera un archivo `.ico` (256×256) por cada imagen en `icons/ico/`.

 ```powershell
 # Ejecutar desde la raíz del proyecto (usa el python del venv si corresponde)
 C:/.../venv/Scripts/python.exe convert_to_ico.py
 ```

 Salida: `icons/ico/` contendrá `nombre.ico` (256×256) por cada imagen encontrada.

 ---

 ## Empaquetado con PyInstaller

 Ejemplo para crear ejecutables sin consola (`--windowed`) e incluyendo la carpeta `icons` en el bundle (esto es importante para que `configure_window()` encuentre los iconos cuando el EXE se ejecute):

 ```powershell
 pyinstaller --onefile --windowed --icon=icons\ico\emisor.ico --add-data "icons;icons" --name micro_emisor interface_emisor.py
 pyinstaller --onefile --windowed --icon=icons\ico\receptor.ico --add-data "icons;icons" --name micro_receptor interface_receptor.py
 ```

 Notas:

 - `--icon` define el icono del archivo `.exe` (Explorador de Windows).
 - Tkinter requiere `root.iconbitmap(path)` para mostrar icono en barra de título / Alt+Tab / barra de tareas.
 - `common.configure_window(root, title, icon_name="...")` busca el icono en:
   - `./icons/<icon_name>` (modo desarrollo)
   - dentro del bundle PyInstaller en `sys._MEIPASS` (cuando `getattr(sys, 'frozen', False)` es True)

 Por eso es importante usar `--add-data "icons;icons"` con PyInstaller.

 ---

 ## Estructura de archivos

 - `interface_emisor.py`
 - `interface_receptor.py`
 - `common.py`
 - `convert_to_ico.py`
 - `icons/` (imágenes y .ico)
 - `icons/ico/` (iconos generados)
 - `requirements.txt`
 - `emisor.spec`, `receptor.spec` (opcional)

 ---

 ## Solución de problemas

 - **Icono en la barra de tareas muestra Python**: ejecuta con `pythonw.exe` o empaqueta con PyInstaller.
 - **Icono no aparece en EXE empacado**: verifica que `icons` se haya incluido con `--add-data "icons;icons"` y que `icon_name` coincida con el archivo `.ico` empaquetado.
 - **PyAudio o dependencias nativas**: en Windows puede ser necesario instalar binarios específicos (por ejemplo usar `pipwin` para `PyAudio`).

 ---
