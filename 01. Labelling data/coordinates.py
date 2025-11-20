import tkinter as tk
from PIL import ImageGrab, ImageTk
import pyautogui
import ctypes
import time
import keyboard 
import json  # <--- NUEVO: Para guardar el archivo

# ==========================================
#  CONFIGURACIÓN INICIAL
# ==========================================
SCREEN_BOX_SIZE = 400  # Tamaño del cuadro rojo

# ==========================================
#  FIX DPI
# ==========================================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except: pass

class MasterConfigurator:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        
        # Estado
        self.is_locked = False
        self.rect_id = None
        self.final_yellow_coords = None
        self.fixed_left = 0
        self.fixed_top = 0

        # --- FASE 1: SEGUIMIENTO DEL MOUSE ---
        self.root.wm_attributes("-alpha", 0.6)
        self.root.config(bg="grey")
        self.root.wm_attributes("-transparentcolor", "grey")
        
        self.frame = tk.Frame(root, bg="grey", highlightthickness=4, highlightbackground="red")
        self.frame.pack(fill="both", expand=True)
        
        self.label = tk.Label(self.frame, text="UBICA Y PRESIONA ENTER (Q para Salir)", 
                              bg="red", fg="white", font=("Arial", 10, "bold"))
        self.label.pack(pady=10)

        # INICIAR BUCLE DE ESCUCHA
        self.update_position_loop()

    def exit_app(self):
        print("Saliendo...")
        self.root.destroy()
        exit()

    def update_position_loop(self):
        if self.is_locked: 
            return
        
        # 1. CHEQUEO DE TECLAS (Fase 1)
        if keyboard.is_pressed('q'):
            self.exit_app()
            return
        
        if keyboard.is_pressed('enter'):
            time.sleep(0.2)
            self.lock_position()
            return
        
        # 2. MOVER VENTANA
        try:
            x, y = pyautogui.position()
            self.fixed_left = x - (SCREEN_BOX_SIZE // 2)
            self.fixed_top = y - (SCREEN_BOX_SIZE // 2)
            self.root.geometry(f"{SCREEN_BOX_SIZE}x{SCREEN_BOX_SIZE}+{self.fixed_left}+{self.fixed_top}")
        except: pass
        
        self.root.after(10, self.update_position_loop)

    # --- TRANSICIÓN A FASE 2 ---
    def lock_position(self):
        self.is_locked = True
        print("Posición fijada. Preparando captura...")
        
        # 1. Ocultar
        self.root.withdraw()
        time.sleep(0.2) 
        
        # 2. Capturar fondo
        bbox = (self.fixed_left, self.fixed_top, 
                self.fixed_left + SCREEN_BOX_SIZE, 
                self.fixed_top + SCREEN_BOX_SIZE)
        self.bg_image = ImageGrab.grab(bbox=bbox, all_screens=True)
        self.photo = ImageTk.PhotoImage(self.bg_image)
        
        # 3. Reaparecer
        self.frame.destroy()
        self.root.deiconify()
        self.root.wm_attributes("-transparentcolor", "")
        self.root.config(bg="white")
        
        # 4. Canvas de Dibujo
        self.canvas = tk.Canvas(self.root, width=SCREEN_BOX_SIZE, height=SCREEN_BOX_SIZE, 
                                cursor="cross", highlightthickness=4, highlightbackground="red")
        self.canvas.pack(fill="both", expand=True)
        
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        
        self.canvas.create_text(SCREEN_BOX_SIZE/2, 20, 
                                text="DIBUJA ZONA AMARILLA Y PULSA ENTER", 
                                fill="yellow", font=("Arial", 8, "bold"))
        self.canvas.create_text(SCREEN_BOX_SIZE/2, 35, 
                                text="(Presiona 'Z' para borrar)", 
                                fill="white", font=("Arial", 7))

        # Binds Mouse (Tkinter)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # Loop Teclado Fase 2
        self.wait_for_final_enter()

    def wait_for_final_enter(self):
        if keyboard.is_pressed('q'):
            self.exit_app()
            return

        if keyboard.is_pressed('enter'):
            time.sleep(0.2)
            self.calculate_and_exit()
            return
        
        # --- NUEVO: BORRAR CON Z ---
        if keyboard.is_pressed('z'):
            time.sleep(0.2) # Evitar rebotes
            self.undo_selection()

        self.root.after(50, self.wait_for_final_enter)
    
    def undo_selection(self):
        """Borra el cuadro amarillo actual para permitir redibujar"""
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
            self.final_yellow_coords = None
            print("-> Cuadro borrado. Puedes dibujar de nuevo.")

    # --- LOGICA DIBUJO ---
    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id: self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, 
                                                    outline="yellow", width=2, dash=(4,4))

    def on_drag(self, event):
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        x1, x2 = sorted([self.start_x, event.x])
        y1, y2 = sorted([self.start_y, event.y])
        self.final_yellow_coords = (x1, y1, x2, y2)

    # --- GUARDADO JSON ---
    def calculate_and_exit(self):
        if not self.final_yellow_coords:
            print("¡Dibuja primero el cuadro amarillo con el mouse!")
            return

        yx1, yy1, yx2, yy2 = self.final_yellow_coords
        
        margin_left = yx1
        margin_top = yy1
        margin_right = SCREEN_BOX_SIZE - yx2
        margin_bottom = SCREEN_BOX_SIZE - yy2
        
        max_shake = int(min(margin_left, margin_top, margin_right, margin_bottom))

        # --- CREAR DICCIONARIO DE DATOS ---
        config_data = {
            "FIXED_LEFT": self.fixed_left,
            "FIXED_TOP": self.fixed_top,
            "MAX_SHAKE": max_shake,
            "SCREEN_BOX_SIZE": SCREEN_BOX_SIZE
        }

        # --- GUARDAR EN JSON ---
        filename = "coordinates_config.json"
        try:
            with open(filename, "w") as f:
                json.dump(config_data, f, indent=4)
            
            print("\n" + "="*50)
            print(f"¡EXITO! Configuración guardada en '{filename}'")
            print("-" * 30)
            print(json.dumps(config_data, indent=4))
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"Error al guardar JSON: {e}")
        
        self.root.destroy()

if __name__ == "__main__":
    print("--- CONFIGURADOR MAESTRO (JSON) ---")
    print("1. Mueve el mouse y presiona ENTER para fijar el recuadro ROJO.")
    print("2. Dibuja el cuadro AMARILLO al borde de la bandeja.")
    print("3. Presiona 'Z' si quieres borrar el cuadro amarillo.")
    print("4. Presiona ENTER para guardar las coordenadas.")
    print("5. Presiona 'Q' para SALIR SIN GUARDAR.")
    root = tk.Tk()
    app = MasterConfigurator(root)
    root.mainloop()