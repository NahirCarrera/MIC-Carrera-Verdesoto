import keyboard
from PIL import ImageGrab, Image
import os
from datetime import datetime
import tkinter as tk
import time
import json
import ctypes 
import random

# ==========================================
#  FIX DE ESCALADO (DPI AWARE)
# ==========================================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except: pass

# ==========================================
#  CONFIGURACIÓN
# ==========================================

FIXED_LEFT = 1010  
FIXED_TOP = 244    
MAX_SHAKE = 31      
SCREEN_BOX_SIZE = 400  

# TUS BANDEJAS MANUALES (Base 320px)
MANUAL_TRAYS = [
    [17, 96, 54, 158], [60, 95, 100, 159], [104, 91, 135, 158], 
    [139, 90, 173, 123], [138, 126, 171, 158], [176, 89, 211, 112], 
    [175, 113, 209, 134], [174, 134, 206, 158], [254, 90, 311, 160]
]

OUTPUT_SIZE = 640

# CARPETAS
IMG_FOLDER = "capturas_yolo"
LABEL_FOLDER = "coordenadas_yolo"
CONFIG_FILE = "config_bandejas.json"
CLASS_ID = 0 

# Teclas
HOTKEY_TOGGLE = "alt+1"   # Muestra/Genera Posición
HOTKEY_ADJUST = "alt+2"   # Ajusta Centro (WASD)
HOTKEY_CAPTURE = "alt+3"  # Captura
HOTKEY_EXIT = "alt+esc"
MOVE_STEP = 2 
# ---------------------

# Variables Globales
overlay_window = None 
overlay_canvas = None 
is_overlay_visible = False 
is_adjust_mode = False       
wasd_hooks = []             

curr_shift_x = 0
curr_shift_y = 0

def get_trays_data():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f), True
        except: pass
    return MANUAL_TRAYS, False

def setup_overlay(window):
    global overlay_canvas
    window.overrideredirect(True)
    window.wm_attributes("-topmost", True)
    window.wm_attributes("-alpha", 0.4) 
    
    # Posición inicial
    refresh_position()
    
    overlay_canvas = tk.Canvas(window, width=SCREEN_BOX_SIZE, height=SCREEN_BOX_SIZE, 
                               bg="red", highlightthickness=3, highlightbackground="red")
    overlay_canvas.pack(fill="both", expand=True)
    
    # Zona segura
    safe = MAX_SHAKE
    overlay_canvas.create_rectangle(safe, safe, SCREEN_BOX_SIZE-safe, SCREEN_BOX_SIZE-safe, 
                                    outline="yellow", dash=(4,4), tags="safe_zone")
    
    draw_green_boxes(0, 0)
    window.withdraw()

def draw_green_boxes(offset_x, offset_y):
    """
    Dibuja las cajas verdes.
    IMPORTANTE: Restamos el offset para que, si la ventana se mueve a la derecha,
    las cajas se dibujen a la izquierda dentro de la ventana, pareciendo fijas en pantalla.
    """
    overlay_canvas.delete("all_boxes")
    trays, from_json = get_trays_data()
    
    if from_json: scale_factor = 1.0 
    else: scale_factor = SCREEN_BOX_SIZE / 320.0 

    for coords in trays:
        x1, y1, x2, y2 = coords
        # Escalar coordenadas base
        sx1, sy1 = int(x1 * scale_factor), int(y1 * scale_factor)
        sx2, sy2 = int(x2 * scale_factor), int(y2 * scale_factor)
        
        # APLICAR EL EFECTO DE "ANCLAJE" (Restar el movimiento de la ventana)
        draw_x1 = sx1 - offset_x
        draw_y1 = sy1 - offset_y
        draw_x2 = sx2 - offset_x
        draw_y2 = sy2 - offset_y
        
        overlay_canvas.create_rectangle(draw_x1, draw_y1, draw_x2, draw_y2, 
                                        outline="#00FF00", width=2, tags="all_boxes")

def refresh_position():
    """Mueve la ventana física (Cuadro Rojo)."""
    if overlay_window:
        x = FIXED_LEFT + curr_shift_x
        y = FIXED_TOP + curr_shift_y
        overlay_window.geometry(f"{SCREEN_BOX_SIZE}x{SCREEN_BOX_SIZE}+{x}+{y}")

def move_center(dx, dy):
    """Mueve el punto de anclaje central."""
    global FIXED_LEFT, FIXED_TOP
    FIXED_LEFT += dx
    FIXED_TOP += dy
    refresh_position()

def hook_wasd():
    wasd_hooks.append(keyboard.add_hotkey('w', lambda: move_center(0, -MOVE_STEP), suppress=True))
    wasd_hooks.append(keyboard.add_hotkey('s', lambda: move_center(0, MOVE_STEP), suppress=True))
    wasd_hooks.append(keyboard.add_hotkey('a', lambda: move_center(-MOVE_STEP, 0), suppress=True))
    wasd_hooks.append(keyboard.add_hotkey('d', lambda: move_center(MOVE_STEP, 0), suppress=True))

def unhook_wasd():
    global wasd_hooks
    for h in wasd_hooks:
        try: keyboard.remove_hotkey(h)
        except: pass
    wasd_hooks = []

def toggle_adjust_mode():
    global is_adjust_mode, is_overlay_visible, curr_shift_x, curr_shift_y
    
    is_adjust_mode = not is_adjust_mode
    
    if is_adjust_mode:
        print("--- MODO AJUSTE (WASD) ---")
        # Resetear offsets para ver el centro real
        curr_shift_x = 0
        curr_shift_y = 0
        
        refresh_position()
        draw_green_boxes(0, 0) # Dibujar sin offset
        
        is_overlay_visible = True
        overlay_window.deiconify()
        overlay_canvas.config(bg="yellow", highlightbackground="yellow")
        hook_wasd()
    else:
        print(f"--- AJUSTE FINALIZADO ---")
        overlay_canvas.config(bg="red", highlightbackground="red")
        unhook_wasd()

def toggle_visible():
    """
    Alt+1: Genera posición, mueve ventana, Y actualiza dibujo interno.
    """
    global is_overlay_visible, curr_shift_x, curr_shift_y
    
    if is_adjust_mode: return

    is_overlay_visible = not is_overlay_visible
    
    if is_overlay_visible:
        # 1. Generar Random
        curr_shift_x = random.randint(-MAX_SHAKE, MAX_SHAKE)
        curr_shift_y = random.randint(-MAX_SHAKE, MAX_SHAKE)
        print(f"Posición Random: Offset ({curr_shift_x}, {curr_shift_y})")
        
        # 2. Mover Ventana (El cuadro rojo se desplaza)
        refresh_position() 
        
        # 3. Redibujar Cajas (Las desplazamos al revés para que parezcan quietas)
        draw_green_boxes(curr_shift_x, curr_shift_y)
        
        overlay_window.deiconify()
    else:
        overlay_window.withdraw()

def generate_yolo_txt(filename_base, trays, from_json, shift_x, shift_y):
    path = os.path.join(LABEL_FOLDER, filename_base + ".txt")
    base_w, base_h = float(SCREEN_BOX_SIZE), float(SCREEN_BOX_SIZE)
    scale_factor = 1.0 if from_json else (SCREEN_BOX_SIZE / 320.0)
    
    with open(path, 'w') as f:
        for coords in trays:
            x1, y1, x2, y2 = coords
            
            # Escalar
            sx1, sy1 = x1 * scale_factor, y1 * scale_factor
            sx2, sy2 = x2 * scale_factor, y2 * scale_factor
            
            # TXT: Calculamos posición relativa al cuadro rojo.
            # Si el cuadro se movió a la derecha (+shift), la bandeja está más a la izquierda (-shift)
            final_x1 = max(0, sx1 - shift_x)
            final_y1 = max(0, sy1 - shift_y)
            final_x2 = min(base_w, sx2 - shift_x)
            final_y2 = min(base_h, sy2 - shift_y)
            
            if final_x2 <= final_x1 or final_y2 <= final_y1: continue 

            # Normalizar
            w, h = final_x2 - final_x1, final_y2 - final_y1
            cx, cy = final_x1 + (w / 2), final_y1 + (h / 2)
            f.write(f"{CLASS_ID} {cx/base_w:.6f} {cy/base_h:.6f} {w/base_w:.6f} {h/base_h:.6f}\n")
    print(f"   -> TXT generado OK")

def take_capture():
    global is_overlay_visible
    
    if is_adjust_mode: return 
    if not is_overlay_visible:
        print("Presiona Alt+1 primero para generar una posición.")
        return

    print("Capturando...")
    
    # Ocultar ventana (ya está posicionada correctamente)
    overlay_window.withdraw()
    is_overlay_visible = False 
    time.sleep(0.1) 
    
    try:
        os.makedirs(IMG_FOLDER, exist_ok=True)
        os.makedirs(LABEL_FOLDER, exist_ok=True)
        
        # Capturar en la posición actual (FIXED + SHIFT)
        cap_left = FIXED_LEFT + curr_shift_x
        cap_top = FIXED_TOP + curr_shift_y
        bbox = (cap_left, cap_top, cap_left + SCREEN_BOX_SIZE, cap_top + SCREEN_BOX_SIZE)
        
        img = ImageGrab.grab(bbox=bbox, all_screens=True)
        img_resized = img.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)

        timestamp = datetime.now().strftime("%d%m%y%H%M%S")
        filename_base = f"img_{timestamp}_s{curr_shift_x}_{curr_shift_y}"
        
        # Guardar
        img_resized.save(os.path.join(IMG_FOLDER, filename_base + ".png"))
        
        # Generar TXT
        trays, from_json = get_trays_data()
        generate_yolo_txt(filename_base, trays, from_json, curr_shift_x, curr_shift_y)
        
        print(f"-> CAPTURA GUARDADA: {filename_base}")
        print("-> Presiona Alt+1 para nueva posición.")

    except Exception as e:
        print(f"Error: {e}")

def exit_program():
    unhook_wasd()
    keyboard.unhook_all()
    if overlay_window: overlay_window.destroy()

def main():
    global overlay_window
    print("--- CAPTURA YOLO FINAL (BANDEJAS VISUALMENTE FIJAS) ---")
    print(f"[{HOTKEY_TOGGLE}] MUESTRA (Calcula nuevo Random)")
    print(f"[{HOTKEY_CAPTURE}] CAPTURA")
    print(f"[{HOTKEY_ADJUST}] AJUSTA CENTRO (WASD)")
    print(f"[{HOTKEY_EXIT}] SALIR")
    
    try:
        overlay_window = tk.Tk()
        setup_overlay(overlay_window)

        keyboard.add_hotkey(HOTKEY_TOGGLE, toggle_visible, suppress=True)
        keyboard.add_hotkey(HOTKEY_CAPTURE, take_capture, suppress=True)
        keyboard.add_hotkey(HOTKEY_ADJUST, toggle_adjust_mode, suppress=True)
        keyboard.add_hotkey(HOTKEY_EXIT, exit_program, suppress=True)

        overlay_window.mainloop()

    except KeyboardInterrupt: pass
    finally:
        keyboard.unhook_all()
        if overlay_window:
            try:
                overlay_window.destroy()
            except:
                pass
if __name__ == "__main__":
    main()