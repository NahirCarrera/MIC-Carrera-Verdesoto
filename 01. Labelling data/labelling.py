import tkinter as tk
from PIL import ImageGrab, ImageTk, Image
import json
import time
import os
import ctypes # <--- IMPORTANTE PARA QUE EL TAMAÑO SEA REAL

# ==========================================
#  FIX DE ESCALADO (DPI AWARE)
# ==========================================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except: pass

# --- CONFIGURACIÓN ---
FIXED_LEFT = 1010 
FIXED_TOP = 244    

# AQUI ESTÁ EL CAMBIO: FIJAMOS EL TAMAÑO DE PANTALLA A 400
OVERLAY_WIDTH = 400
OVERLAY_HEIGHT = 400

CONFIG_FILE = "config_bandejas.json"

class TrayEditor:
    def __init__(self, root):
        self.root = root
        self.root.withdraw() # 1. OCULTAR VENTANA AL INICIO
        
        self.rectangles = [] 
        self.current_rect = None
        self.start_x = None
        self.start_y = None

        # Configurar ventana sin bordes
        self.root.overrideredirect(True)
        self.root.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}+{FIXED_LEFT}+{FIXED_TOP}")
        
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
        self.root.bind("<Escape>", lambda e: self.root.destroy()) # Salir

        print("--- EDITOR DE BANDEJAS (400x400) ---")
        print("1. Dibuja recuadros VERDES sobre cada ingrediente.")
        print("2. Presiona 'Z' para borrar el último.")
        print("3. Presiona 'S' para GUARDAR y salir.")
        
        # 4. MOSTRAR LA VENTANA
        self.root.deiconify()

    def take_clean_screenshot(self):
        """Se asegura de que la pantalla esté limpia antes de capturar."""
        print("Preparando captura... espera un momento...")
        time.sleep(0.5) 
        
        # Capturar SOLO la zona fija de 400x400
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
        
        self.rectangles.append({'coords': [x1, y1, x2, y2], 'id': self.current_rect})
        print(f"Bandeja registrada: {x1},{y1} - {x2},{y2}")
        self.current_rect = None

    def undo_last(self, event):
        if self.rectangles:
            last = self.rectangles.pop()
            self.canvas.delete(last['id'])
            print("Última bandeja eliminada.")

    def save_config(self, event):
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