import tkinter as tk
from PIL import ImageGrab, ImageTk, Image
import json
import time
import os
import ctypes
import keyboard # <--- IMPORTANTE: Necesario para detectar Alt+1

# ==========================================
#  FIX DE ESCALADO (DPI AWARE)
# ==========================================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except: pass

# ==========================================
#  CONFIGURACIÓN Y CARGA DE DATOS
# ==========================================

# Archivos
CONFIG_FILE = "config_bandejas.json"          # Donde guardamos los recuadros
COORD_CONFIG_FILE = "coordinates_config.json" # De donde leemos la posición de la ventana

# Valores por defecto (se usarán si no existe el JSON)
FIXED_LEFT = 1010 
FIXED_TOP = 244    
SCREEN_BOX_SIZE = 400 # Usamos esta variable para ancho y alto

# Cargar configuración compartida
if os.path.exists(COORD_CONFIG_FILE):
    try:
        with open(COORD_CONFIG_FILE, 'r') as f:
            data = json.load(f)
            FIXED_LEFT = data.get("FIXED_LEFT", FIXED_LEFT)
            FIXED_TOP = data.get("FIXED_TOP", FIXED_TOP)
            SCREEN_BOX_SIZE = data.get("SCREEN_BOX_SIZE", SCREEN_BOX_SIZE)
        print(f"-> Configuración de posición cargada: {COORD_CONFIG_FILE}")
    except Exception as e:
        print(f"Error leyendo config de coordenadas: {e}")
else:
    print("-> Usando coordenadas por defecto (No se encontró JSON de posición)")

# Asignamos el tamaño
OVERLAY_WIDTH = SCREEN_BOX_SIZE
OVERLAY_HEIGHT = SCREEN_BOX_SIZE

# ==========================================
#  CLASE DEL EDITOR
# ==========================================

class TrayEditor:
    def __init__(self, root):
        self.root = root
        self.root.withdraw() # 1. OCULTAR VENTANA AL INICIO
        
        self.rectangles = [] 
        self.current_rect = None
        self.start_x = None
        self.start_y = None

        # Configurar ventana sin bordes y SIEMPRE VISIBLE (TOPMOST)
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}+{FIXED_LEFT}+{FIXED_TOP}")
        
        # --- ESPERA ACTIVA ---
        print(f"--- EDITOR DE BANDEJAS ({OVERLAY_WIDTH}x{OVERLAY_HEIGHT}) ---")
        print(f"Ubicación: {FIXED_LEFT}, {FIXED_TOP}")
        print("\n" + "="*50)
        print("   ESPERANDO... PON EL JUEGO EN PANTALLA.")
        print("   >>> PRESIONA 'ALT+1' PARA CAPTURAR <<<")
        print("="*50 + "\n")
        
        # Bloquea el programa hasta que presiones Alt+1
        keyboard.wait('alt+1')
        time.sleep(0.3) # Pequeña pausa para asegurar que soltaste las teclas
        
        # 2. TOMAR LA FOTO LIMPIA
        self.take_clean_screenshot()
        
        # 3. CONFIGURAR EL CANVAS
        self.canvas = tk.Canvas(root, width=OVERLAY_WIDTH, height=OVERLAY_HEIGHT, 
                                highlightthickness=3, highlightbackground="red", cursor="cross")
        self.canvas.pack(fill="both", expand=True)
        
        # Poner la captura como fondo
        self.canvas.create_image(0, 0, image=self.photo_ref, anchor="nw")
        
        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        
        self.root.bind("s", self.save_config)  # Guardar
        self.root.bind("z", self.undo_last)    # Deshacer
        self.root.bind("q", lambda e: self.root.destroy()) # Salir sin guardar
        self.root.bind("<Escape>", lambda e: self.root.destroy()) # Salir

        print("MODO EDICIÓN ACTIVO:")
        print("1. Dibuja recuadros VERDES sobre cada ingrediente.")
        print("2. Presiona 'Z' para borrar el último.")
        print("3. Presiona 'S' para GUARDAR y salir.")
        print("4. Presiona 'Q' para SALIR SIN GUARDAR.")
        
        # 4. MOSTRAR LA VENTANA
        self.root.deiconify()
        
        # Forzar que la ventana suba al frente
        self.root.lift()
        self.root.focus_force()

    def take_clean_screenshot(self):
        """Se asegura de que la pantalla esté limpia antes de capturar."""
        print("Capturando fondo...")
        
        # Capturar SOLO la zona fija definida por el JSON
        bbox = (FIXED_LEFT, FIXED_TOP, FIXED_LEFT + OVERLAY_WIDTH, FIXED_TOP + OVERLAY_HEIGHT)
        self.image_ref = ImageGrab.grab(bbox=bbox, all_screens=True)
        self.photo_ref = ImageTk.PhotoImage(self.image_ref)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, 
            outline="#00FF00", width=2
        )

    def on_move_press(self, event):
        self.canvas.coords(self.current_rect, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        
        # Ordenar coordenadas
        x1, x2 = sorted([self.start_x, end_x])
        y1, y2 = sorted([self.start_y, end_y])
        
        # Evitar clics accidentales (puntos sin tamaño)
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            return

        self.rectangles.append({'coords': [x1, y1, x2, y2], 'id': self.current_rect})
        print(f"Bandeja registrada: {x1},{y1} - {x2},{y2}")
        self.current_rect = None

    def undo_last(self, event):
        if self.rectangles:
            last = self.rectangles.pop()
            self.canvas.delete(last['id'])
            print("Última bandeja eliminada.")

    def save_config(self, event):
        # Extraemos solo las coordenadas para el JSON
        data = [r['coords'] for r in self.rectangles]
        
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f)
            print(f"\n¡ÉXITO! Se guardaron {len(data)} bandejas en '{CONFIG_FILE}'.")
            self.root.destroy()
        except Exception as e:
            print(f"Error al guardar: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TrayEditor(root)
    root.mainloop()