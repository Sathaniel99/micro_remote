"""
Script para convertir imágenes JPEG/JPG a formato ICO válido para Tkinter

Uso:
    python convert_to_ico.py

Busca todas las imágenes (.jpeg, .jpg) en la carpeta 'icons' y las convierte
a formato ICO con múltiples resoluciones. Los archivos ICO se guardan en la
carpeta 'icons/ico' (se crea automáticamente si no existe).
"""

from PIL import Image
import os
from pathlib import Path


def convert_jpeg_to_ico(jpeg_path, ico_path, size=(256, 256)):
    """
    Convierte una imagen JPEG a ICO con múltiples resoluciones.
    
    Args:
        jpeg_path: ruta al archivo JPEG
        ico_path: ruta de salida del archivo ICO
        size: tamaño base (será escalado a múltiples resoluciones)
    """
    try:
        # Abrir imagen JPEG
        img = Image.open(jpeg_path)
        
        # Convertir a RGB si es necesario
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Crear múltiples tamaños para el ICO
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        ico_images = []
        
        for size in sizes:
            # Redimensionar manteniendo aspecto
            img_resized = img.copy()
            img_resized.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Crear canvas con el tamaño exacto
            ico_img = Image.new('RGB', size, (255, 255, 255))
            offset = ((size[0] - img_resized.width) // 2, (size[1] - img_resized.height) // 2)
            ico_img.paste(img_resized, offset)
            ico_images.append(ico_img)
        
        # Guardar como ICO con todos los tamaños (multi-res)
        try:
            ico_images[0].save(ico_path, sizes=sizes)
            print(f"✓ Convertido (multi): {os.path.basename(jpeg_path)} → {os.path.basename(ico_path)}")
        except Exception:
            # Si falla la creación multi-res, no detener el resto
            print(f"⚠ No se pudo crear multi-res ICO para {os.path.basename(jpeg_path)}")
        return True
        
    except Exception as e:
        print(f"✗ Error al convertir {jpeg_path}: {e}")
        return False


def main():
    """Busca y convierte todas las imágenes JPEG/JPG a ICO."""
    # Obtener ruta del script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(script_dir, 'icons')
    output_dir = os.path.join(icons_dir, 'ico_output')
    
    # Validar que la carpeta 'icons' existe
    if not os.path.isdir(icons_dir):
        print(f"✗ Error: No se encontró la carpeta '{icons_dir}'")
        return
    
    # Crear carpeta de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    print(f"Carpeta de salida: {output_dir}\n")

    # Extensiones a buscar
    image_extensions = ('.jpeg', '.jpg', '.JPG', '.JPEG')

    # Buscar todas las imágenes
    image_files = []
    for ext in image_extensions:
        image_files.extend(Path(icons_dir).glob(f'*{ext}'))

    if not image_files:
        print(f"⚠ No se encontraron imágenes (.jpeg, .jpg) en {icons_dir}")
        return

    print(f"Se encontraron {len(image_files)} imagen(es) para convertir:\n")

    converted_count = 0
    failed_count = 0

    # Crear un ICO que incluya la resolución máxima 256x256 (solo esa resolución)
    sizes = [(256, 256)]

    for image_path in sorted(image_files):
        base_name = image_path.stem
        multi_filename = f"{base_name}.ico"
        multi_path = os.path.join(output_dir, multi_filename)

        # Regenerar siempre (si prefieres evitar sobrescribir, comprobar existencia aquí)
        try:
            img = Image.open(str(image_path))
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Preparar la imagen para 256x256 (mantener aspecto, centrar)
            s = sizes[0]
            img_resized = img.copy()
            img_resized.thumbnail(s, Image.Resampling.LANCZOS)
            ico_img = Image.new('RGB', s, (255, 255, 255))
            offset = ((s[0] - img_resized.width) // 2, (s[1] - img_resized.height) // 2)
            ico_img.paste(img_resized, offset)

            # Guardar ICO con la resolución 256x256 (archivo único por imagen)
            ico_img.save(multi_path, sizes=sizes)
            print(f"✓ Convertido (256x256): {os.path.basename(image_path)} → {multi_filename}")
            converted_count += 1
        except Exception as e:
            print(f"✗ Error creando {multi_filename}: {e}")
            failed_count += 1
    
    # Resumen
    print(f"\n{'='*50}")
    print(f"Conversión completada:")
    print(f"  ✓ Exitosas: {converted_count}")
    if failed_count > 0:
        print(f"  ✗ Fallidas: {failed_count}")
    print(f"  📁 Salida: {output_dir}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

