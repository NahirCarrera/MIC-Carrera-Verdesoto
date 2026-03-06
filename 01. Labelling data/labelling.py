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
CONFIG_FILE = "labelling_config.json"         # Donde guardamos los recuadros + clases
COORD_CONFIG_FILE = "coordinates_config.json" # De donde leemos la posición de la ventana

# ==========================================
#  MAPEO DE CLASES (INGREDIENTES)
# ==========================================
CLASS_MAP = {
    0: "tomato",
    1: "lettuce",
    2: "onion",
    3: "pickles",
    4: "pepper",
    5: "bacon",
    6: "ketchup",
    7: "mayo",
    8: "jalapeno"
}

# Colores distintos por clase para diferenciar visualmente
CLASS_COLORS = {
    0: "#FF4444",  # tomato   → rojo
    1: "#0604A8",  # lettuce  → verde claro
    2: "#FFFFFF",  # onion    → blanco
    3: "#228B22",  # pickles  → verde oscuro
    4: "#FA00AF",  # pepper   → naranja
    5: "#8B0000",  # bacon    → rojo oscuro
    6: "#FF0000",  # ketchup  → rojo brillante
    7: "#FFFFAA",  # mayo     → amarillo claro
    8: "#967FE7"   # jalapeno → verde lima
}

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
        self.pending_rect = None  # Recuadro esperando asignación de clase

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

        # Bindings para asignar clase (teclas 0-7)
        for key in range(9):
            self.root.bind(str(key), self.assign_class)

        self._print_instructions()
        
        # 4. MOSTRAR LA VENTANA
        self.root.deiconify()
        
        # Forzar que la ventana suba al frente
        self.root.lift()
        self.root.focus_force()

    def _print_instructions(self):
        print("\n" + "="*50)
        print("  MODO EDICIÓN ACTIVO")
        print("="*50)
        print("\n  CLASES DISPONIBLES:")
        for cid, name in CLASS_MAP.items():
            print(f"    [{cid}] {name}")
        print("\n  FLUJO:")
        print("  1. Dibuja un recuadro (clic + arrastrar)")
        print("  2. Presiona [0-7] para asignar la clase")
        print("  3. Repite para cada bandeja")
        print("")
        print("  [Z] Deshacer último    [S] Guardar    [Q/ESC] Salir")
        print("="*50 + "\n")

    def take_clean_screenshot(self):
        """Se asegura de que la pantalla esté limpia antes de capturar."""
        print("Capturando fondo...")
        
        # Capturar SOLO la zona fija definida por el JSON
        bbox = (FIXED_LEFT, FIXED_TOP, FIXED_LEFT + OVERLAY_WIDTH, FIXED_TOP + OVERLAY_HEIGHT)
        self.image_ref = ImageGrab.grab(bbox=bbox, all_screens=True)
        self.photo_ref = ImageTk.PhotoImage(self.image_ref)

    def on_button_press(self, event):
        # No permitir dibujar si hay un recuadro pendiente de clase
        if self.pending_rect is not None:
            print("⚠️  Primero asigna clase al recuadro actual (tecla 0-7)")
            return
        self.start_x = event.x
        self.start_y = event.y
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, 
            outline="#FFFF00", width=2, dash=(4, 4)  # Amarillo punteado = pendiente
        )

    def on_move_press(self, event):
        if self.current_rect:
            self.canvas.coords(self.current_rect, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        if self.current_rect is None:
            return
        end_x, end_y = (event.x, event.y)
        
        # Ordenar coordenadas
        x1, x2 = sorted([self.start_x, end_x])
        y1, y2 = sorted([self.start_y, end_y])
        
        # Evitar clics accidentales (puntos sin tamaño)
        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            return

        # Guardar como pendiente (esperando asignación de clase)
        self.pending_rect = {
            'coords': [x1, y1, x2, y2], 
            'id': self.current_rect,
            'class_id': None
        }
        self.current_rect = None
        print(f"📦 Recuadro dibujado: [{x1},{y1} - {x2},{y2}]  →  Presiona [0-7] para asignar clase")

    def assign_class(self, event):
        """Asigna clase al recuadro pendiente cuando se presiona 0-7."""
        if self.pending_rect is None:
            return  # No hay recuadro pendiente
        
        class_id = int(event.char)
        class_name = CLASS_MAP.get(class_id, "???")
        color = CLASS_COLORS.get(class_id, "#00FF00")
        
        # Actualizar el recuadro visual: color sólido de la clase
        rect_id = self.pending_rect['id']
        x1, y1, x2, y2 = self.pending_rect['coords']
        self.canvas.delete(rect_id)
        
        new_rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2, outline=color, width=2
        )
        
        # Agregar label de texto
        label_id = self.canvas.create_text(
            x1 + 2, y1 + 2, 
            text=f"{class_id}:{class_name}", 
            anchor="nw", fill=color, 
            font=("Arial", 8, "bold")
        )
        
        # Registrar la bandeja con su clase
        self.pending_rect['class_id'] = class_id
        self.pending_rect['id'] = new_rect_id
        self.pending_rect['label_id'] = label_id
        self.rectangles.append(self.pending_rect)
        self.pending_rect = None
        
        print(f"✅ Bandeja #{len(self.rectangles)} → Clase {class_id} ({class_name})")

    def undo_last(self, event):
        # Si hay un recuadro pendiente, borrarlo primero
        if self.pending_rect is not None:
            self.canvas.delete(self.pending_rect['id'])
            self.pending_rect = None
            print("🗑️  Recuadro pendiente eliminado.")
            return
        
        if self.rectangles:
            last = self.rectangles.pop()
            self.canvas.delete(last['id'])
            if 'label_id' in last:
                self.canvas.delete(last['label_id'])
            class_name = CLASS_MAP.get(last['class_id'], '???')
            print(f"🗑️  Eliminada bandeja {class_name} (clase {last['class_id']})")

    def save_config(self, event):
        # Verificar que no haya recuadros pendientes sin clase
        if self.pending_rect is not None:
            print("⚠️  ¡Hay un recuadro sin clase asignada! Presiona [0-7] primero.")
            return
        
        if not self.rectangles:
            print("⚠️  No hay bandejas registradas. Dibuja al menos una.")
            return
        
        # Formato: [[x1, y1, x2, y2, class_id], ...]
        data = [r['coords'] + [r['class_id']] for r in self.rectangles]
        
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"\n{'='*50}")
            print(f"  ¡ÉXITO! Se guardaron {len(data)} bandejas en '{CONFIG_FILE}'")
            print(f"{'='*50}")
            for i, r in enumerate(self.rectangles):
                cid = r['class_id']
                cname = CLASS_MAP.get(cid, '???')
                coords = r['coords']
                print(f"  Bandeja {i+1}: {cname} (clase {cid}) → {coords}")
            print(f"{'='*50}\n")

            self.root.destroy()
        except Exception as e:
            print(f"Error al guardar: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TrayEditor(root)
    root.mainloop()