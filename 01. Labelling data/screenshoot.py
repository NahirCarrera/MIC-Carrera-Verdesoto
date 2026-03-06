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
#  CONFIGURACIÓN Y CONSTANTES
# ==========================================

# Archivos
IMG_FOLDER = "capturas_yolo"
LABEL_FOLDER = "coordenadas_yolo"
TRAYS_CONFIG_FILE = "labelling_config.json" # Configuración de las cajas verdes
COORD_CONFIG_FILE = "coordinates_config.json" # NUEVO: Configuración de posición y tamaño

# Valores por defecto (se sobreescriben si existe el JSON)
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

# Mapeo de clases (debe coincidir con labelling.py)
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

# Teclas
HOTKEY_CLEAN = "1"        # Captura LIMPIA (con etiquetas YOLO)
HOTKEY_OBSTRUCTED = "2"   # Captura OBSTRUIDA (negative sample, sin etiquetas)
HOTKEY_ADJUST = "alt+2"   # Ajustar Centro (WASD)
HOTKEY_EXIT = "alt+esc"
MOVE_STEP = 2 

# Variables Globales de Estado
overlay_window = None 
overlay_canvas = None 
is_adjust_mode = False       
wasd_hooks = []

# Contadores de capturas
count_clean = 0
count_obstructed = 0

# Ventana HUD (contador en pantalla)
hud_window = None
hud_label = None

# ==========================================
#  GESTIÓN DE CONFIGURACIÓN (JSON)
# ==========================================

def load_main_config():
    """Carga FIXED_LEFT, FIXED_TOP, MAX_SHAKE, SCREEN_BOX_SIZE desde JSON"""
    global FIXED_LEFT, FIXED_TOP, MAX_SHAKE, SCREEN_BOX_SIZE
    
    if os.path.exists(COORD_CONFIG_FILE):
        try:
            with open(COORD_CONFIG_FILE, 'r') as f:
                data = json.load(f)
                # Usamos .get() para mantener el valor por defecto si falta la clave
                FIXED_LEFT = data.get("FIXED_LEFT", FIXED_LEFT)
                FIXED_TOP = data.get("FIXED_TOP", FIXED_TOP)
                MAX_SHAKE = data.get("MAX_SHAKE", MAX_SHAKE)
                SCREEN_BOX_SIZE = data.get("SCREEN_BOX_SIZE", SCREEN_BOX_SIZE)
            print(f"-> Configuración cargada: {COORD_CONFIG_FILE}")
        except Exception as e:
            print(f"Error leyendo {COORD_CONFIG_FILE}: {e}")
    else:
        print("-> Usando configuración por defecto (No se encontró JSON)")

def save_main_config():
    """Guarda la configuración actual (útil tras mover con WASD)"""
    data = {
        "FIXED_LEFT": FIXED_LEFT,
        "FIXED_TOP": FIXED_TOP,
        "MAX_SHAKE": MAX_SHAKE,
        "SCREEN_BOX_SIZE": SCREEN_BOX_SIZE
    }
    try:
        with open(COORD_CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"-> Configuración guardada en {COORD_CONFIG_FILE}")
    except Exception as e:
        print(f"Error guardando config: {e}")

def get_trays_data():
    """Carga las coordenadas de las bandejas (cajas verdes)"""
    if os.path.exists(TRAYS_CONFIG_FILE):
        try:
            with open(TRAYS_CONFIG_FILE, 'r') as f:
                return json.load(f), True
        except: pass
    return MANUAL_TRAYS, False

def count_existing_images():
    """Escanea la carpeta de imágenes y cuenta cuántas clean/obstructed ya existen."""
    global count_clean, count_obstructed
    count_clean = 0
    count_obstructed = 0
    
    if not os.path.exists(IMG_FOLDER):
        return
    
    for fname in os.listdir(IMG_FOLDER):
        if not fname.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        if '_obstr_' in fname:
            count_obstructed += 1
        elif '_clean_' in fname:
            count_clean += 1
        else:
            # Imágenes antiguas sin tag se cuentan como clean
            count_clean += 1
    
    print(f"-> Imágenes existentes detectadas: {count_clean} clean, {count_obstructed} obstructed")

# ==========================================
#  INTERFAZ Y LÓGICA
# ==========================================

def setup_overlay(window):
    global overlay_canvas
    window.overrideredirect(True)
    window.wm_attributes("-topmost", True)
    window.wm_attributes("-alpha", 0.5)
    
    # Posición inicial usando las variables cargadas
    window.geometry(f"{SCREEN_BOX_SIZE}x{SCREEN_BOX_SIZE}+{FIXED_LEFT}+{FIXED_TOP}")
    
    overlay_canvas = tk.Canvas(window, width=SCREEN_BOX_SIZE, height=SCREEN_BOX_SIZE, 
                               bg="cyan", highlightthickness=3, highlightbackground="cyan")
    overlay_canvas.pack(fill="both", expand=True)
    
    # Zona segura visual
    safe = MAX_SHAKE
    overlay_canvas.create_rectangle(safe, safe, SCREEN_BOX_SIZE-safe, SCREEN_BOX_SIZE-safe, 
                                    outline="yellow", dash=(4,4), tags="safe_zone")
    
    draw_green_boxes(0, 0)
    window.withdraw()

def setup_hud(parent):
    """Crea una ventana HUD flotante con el contador en pantalla."""
    global hud_window, hud_label
    
    hud_window = tk.Toplevel(parent)
    hud_window.overrideredirect(True)
    hud_window.wm_attributes("-topmost", True)
    hud_window.wm_attributes("-alpha", 0.85)
    hud_window.config(bg="#1a1a2e")
    
    # Posicionar arriba a la izquierda de la zona de captura
    hud_x = FIXED_LEFT
    hud_y = max(0, FIXED_TOP - 75)
    hud_window.geometry(f"320x65+{hud_x}+{hud_y}")
    
    hud_label = tk.Label(
        hud_window, 
        text="", 
        font=("Consolas", 10), 
        fg="#00FF00", 
        bg="#1a1a2e",
        justify="left",
        anchor="w"
    )
    hud_label.pack(fill="both", expand=True, padx=6, pady=4)
    
    update_hud()

def update_hud():
    """Actualiza el texto del HUD con los contadores actuales."""
    if hud_label is None:
        return
    
    total = count_clean + count_obstructed
    if total == 0:
        pct_clean = 0
        pct_obstr = 0
    else:
        pct_clean = (count_clean / total) * 100
        pct_obstr = (count_obstructed / total) * 100
    
    # Barra visual compacta
    bar_len = 20
    filled = int(bar_len * pct_clean / 100) if total > 0 else 0
    bar = '█' * filled + '░' * (bar_len - filled)
    
    # Indicador de proporción
    if total < 10:
        status = "⏳"
    elif 5 <= pct_obstr <= 20:
        status = "✅"
    else:
        status = "⚠️"
    
    text = (
        f"CLEAN: {count_clean:>4} ({pct_clean:4.1f}%)  │  TOTAL: {total}\n"
        f"OBSTR: {count_obstructed:>4} ({pct_obstr:4.1f}%)  │  {status} Ratio\n"
        f"[{bar}]"
    )
    
    hud_label.config(text=text)
    
    # Reposicionar HUD por si se movió con WASD
    hud_x = FIXED_LEFT
    hud_y = max(0, FIXED_TOP - 75)
    hud_window.geometry(f"320x65+{hud_x}+{hud_y}")

def draw_green_boxes(offset_x, offset_y):
    overlay_canvas.delete("all_boxes")
    trays, from_json = get_trays_data()
    
    if from_json: scale_factor = 1.0 
    else: scale_factor = SCREEN_BOX_SIZE / 320.0 

    for entry in trays:
        # Soporta formato nuevo [x1,y1,x2,y2,class_id] y antiguo [x1,y1,x2,y2]
        x1, y1, x2, y2 = entry[0], entry[1], entry[2], entry[3]
        
        sx1, sy1 = int(x1 * scale_factor), int(y1 * scale_factor)
        sx2, sy2 = int(x2 * scale_factor), int(y2 * scale_factor)
        
        draw_x1 = sx1 - offset_x
        draw_y1 = sy1 - offset_y
        draw_x2 = sx2 - offset_x
        draw_y2 = sy2 - offset_y
        
        overlay_canvas.create_rectangle(draw_x1, draw_y1, draw_x2, draw_y2, 
                                        outline="#00FF00", width=2, tags="all_boxes")

def refresh_position(x, y):
    if overlay_window:
        overlay_window.geometry(f"{SCREEN_BOX_SIZE}x{SCREEN_BOX_SIZE}+{x}+{y}")

# --- WASD CENTRO ---
def move_center(dx, dy):
    global FIXED_LEFT, FIXED_TOP
    FIXED_LEFT += dx
    FIXED_TOP += dy
    refresh_position(FIXED_LEFT, FIXED_TOP)

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
    global is_adjust_mode
    is_adjust_mode = not is_adjust_mode
    
    if is_adjust_mode:
        print("--- MODO AJUSTE (WASD) ---")
        refresh_position(FIXED_LEFT, FIXED_TOP)
        draw_green_boxes(0, 0)
        overlay_window.deiconify()
        overlay_canvas.config(bg="yellow", highlightbackground="yellow")
        hook_wasd()
    else:
        print(f"--- CENTRO FIJADO Y GUARDADO ---")
        save_main_config() # Guardar cambios al salir del modo ajuste
        overlay_window.withdraw()
        unhook_wasd()

def generate_yolo_txt(filename_base, trays, from_json, shift_x, shift_y):
    path = os.path.join(LABEL_FOLDER, filename_base + ".txt")
    base_w, base_h = float(SCREEN_BOX_SIZE), float(SCREEN_BOX_SIZE)
    scale_factor = 1.0 if from_json else (SCREEN_BOX_SIZE / 320.0)
    
    with open(path, 'w') as f:
        for entry in trays:
            # Nuevo formato: [x1, y1, x2, y2, class_id]
            # Fallback al antiguo: [x1, y1, x2, y2] (clase 0)
            if len(entry) >= 5:
                x1, y1, x2, y2, class_id = entry[0], entry[1], entry[2], entry[3], entry[4]
            else:
                x1, y1, x2, y2 = entry[0], entry[1], entry[2], entry[3]
                class_id = 0
            
            sx1, sy1 = x1 * scale_factor, y1 * scale_factor
            sx2, sy2 = x2 * scale_factor, y2 * scale_factor
            
            final_x1 = max(0, sx1 - shift_x)
            final_y1 = max(0, sy1 - shift_y)
            final_x2 = min(base_w, sx2 - shift_x)
            final_y2 = min(base_h, sy2 - shift_y)
            
            if final_x2 <= final_x1 or final_y2 <= final_y1: continue 

            w, h = final_x2 - final_x1, final_y2 - final_y1
            cx, cy = final_x1 + (w / 2), final_y1 + (h / 2)
            f.write(f"{class_id} {cx/base_w:.6f} {cy/base_h:.6f} {w/base_w:.6f} {h/base_h:.6f}\n")

def print_counter_status():
    """Imprime el estado actual de capturas con proporción."""
    total = count_clean + count_obstructed
    if total == 0:
        pct_clean = 0
        pct_obstr = 0
    else:
        pct_clean = (count_clean / total) * 100
        pct_obstr = (count_obstructed / total) * 100
    
    bar_len = 30
    filled = int(bar_len * pct_clean / 100) if total > 0 else 0
    bar = '█' * filled + '░' * (bar_len - filled)
    
    print(f"\n  ┌───────────────────────────────────────────┐")
    print(f"  │  CLEAN: {count_clean:>4}  ({pct_clean:5.1f}%)                  │")
    print(f"  │  OBSTR: {count_obstructed:>4}  ({pct_obstr:5.1f}%)  │ Total: {total:<4} │")
    print(f"  │  [{bar}]  │")
    print(f"  └───────────────────────────────────────────┘")
    
    # Advertencia si la proporción se desbalancea
    if total >= 10 and pct_obstr > 20:
        print(f"  ⚠️  Muchas obstruidas ({pct_obstr:.0f}%). Recomendado: 10-15% del total.")
    elif total >= 10 and pct_obstr < 5:
        print(f"  ⚠️  Pocas obstruidas ({pct_obstr:.0f}%). Recomendado: 10-15% del total.")

def take_capture(mode="clean"):
    """
    mode='clean'      -> Captura + etiquetas YOLO (tecla 1)
    mode='obstructed'  -> Captura + .txt vacío / negative sample (tecla 2)
    """
    global count_clean, count_obstructed
    if is_adjust_mode: return 

    try:
        os.makedirs(IMG_FOLDER, exist_ok=True)
        os.makedirs(LABEL_FOLDER, exist_ok=True)
        
        # 1. GENERAR POSICIÓN ALEATORIA (shake en ambos modos)
        shift_x = random.randint(-MAX_SHAKE, MAX_SHAKE)
        shift_y = random.randint(-MAX_SHAKE, MAX_SHAKE)
        
        temp_left = FIXED_LEFT + shift_x
        temp_top = FIXED_TOP + shift_y
        
        # 2. FEEDBACK VISUAL
        refresh_position(temp_left, temp_top)
        draw_green_boxes(shift_x, shift_y)
        
        fb_color = "cyan" if mode == "clean" else "red"
        overlay_canvas.config(bg=fb_color, highlightbackground=fb_color)
        overlay_window.deiconify()
        overlay_window.update()
        time.sleep(0.15) 
        
        # 3. OCULTAR
        overlay_window.withdraw()
        time.sleep(0.1)
        
        # 4. CAPTURAR
        bbox = (temp_left, temp_top, temp_left + SCREEN_BOX_SIZE, temp_top + SCREEN_BOX_SIZE)
        img = ImageGrab.grab(bbox=bbox, all_screens=True)
        img_resized = img.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)

        # 5. GUARDAR IMAGEN
        tag = "clean" if mode == "clean" else "obstr"
        timestamp = datetime.now().strftime("%d%m%y%H%M%S")
        filename_base = f"img_{timestamp}_{tag}_s{shift_x}_{shift_y}"
        
        img_resized.save(os.path.join(IMG_FOLDER, filename_base + ".png"))
        
        # 6. GUARDAR ETIQUETAS + ACTUALIZAR CONTADOR
        if mode == "clean":
            trays, from_json = get_trays_data()
            generate_yolo_txt(filename_base, trays, from_json, shift_x, shift_y)
            count_clean += 1
            print(f"✅ Guardado: CLEAN (Bandeja válida) -> {filename_base} (Offset {shift_x},{shift_y})")
        else:
            empty_label_path = os.path.join(LABEL_FOLDER, filename_base + ".txt")
            open(empty_label_path, 'w').close()
            count_obstructed += 1
            print(f"⛔ Guardado: OBSTRUCTED (Background Image) -> {filename_base} (Offset {shift_x},{shift_y})")
        
        print_counter_status()
        update_hud()

    except Exception as e:
        print(f"Error: {e}")
        overlay_window.withdraw()

def exit_program():
    save_main_config() # Guardar antes de salir por seguridad
    unhook_wasd()
    keyboard.unhook_all()
    if hud_window:
        try: hud_window.destroy()
        except: pass
    if overlay_window: overlay_window.destroy()

def main():
    global overlay_window
    
    # Cargar configuración antes de iniciar la GUI
    load_main_config()
    
    print("--- CAPTURA YOLO (MANUAL: CLEAN / OBSTRUCTED) ---")
    print(f"Config cargada desde: {COORD_CONFIG_FILE}")
    print(f"")
    print(f"  [{HOTKEY_CLEAN}]  CAPTURA CLEAN    (Bandeja válida + etiquetas YOLO)")
    print(f"  [{HOTKEY_OBSTRUCTED}]  CAPTURA OBSTRUCTED (Negative sample, sin etiquetas)")
    print(f"  [{HOTKEY_ADJUST}]  AJUSTAR CENTRO   (WASD para mover)")
    print(f"  [{HOTKEY_EXIT}]  SALIR")
    print(f"")
    print(">>> Esperando input... <<<")
    
    # Contar imágenes existentes antes de empezar
    count_existing_images()
    print_counter_status()
    
    try:
        overlay_window = tk.Tk()
        setup_overlay(overlay_window)
        setup_hud(overlay_window)

        keyboard.add_hotkey(HOTKEY_CLEAN, lambda: take_capture("clean"), suppress=True)
        keyboard.add_hotkey(HOTKEY_OBSTRUCTED, lambda: take_capture("obstructed"), suppress=True)
        keyboard.add_hotkey(HOTKEY_ADJUST, toggle_adjust_mode, suppress=True)
        keyboard.add_hotkey(HOTKEY_EXIT, exit_program, suppress=True)

        overlay_window.mainloop()

    except KeyboardInterrupt: pass
    finally:
        save_main_config()
        keyboard.unhook_all()
        if overlay_window:
            try: overlay_window.destroy()
            except: pass

if __name__ == "__main__":
    main()