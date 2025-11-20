import cv2
import os
import glob

# --- CONFIGURACIÓN ---
IMG_FOLDER = "capturas_yolo"
LABEL_FOLDER = "coordenadas_yolo"

def load_images():
    # Buscar todas las imágenes png/jpg
    extensions = ['*.png', '*.jpg', '*.jpeg']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(IMG_FOLDER, ext)))
    
    # Ordenar por fecha (las más nuevas al final)
    files.sort(key=os.path.getmtime)
    return files

def draw_yolo_labels(img, label_path):
    h_img, w_img, _ = img.shape
    
    if not os.path.exists(label_path):
        # Escribir en la imagen que falta el txt
        cv2.putText(img, "NO TXT FOUND", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return img

    with open(label_path, 'r') as f:
        lines = f.readlines()
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) != 5: continue

            # YOLO Format: class x_center y_center width height (Normalizados)
            x_center_norm = float(parts[1])
            y_center_norm = float(parts[2])
            width_norm = float(parts[3])
            height_norm = float(parts[4])

            # Des-normalizar a píxeles
            x_center = int(x_center_norm * w_img)
            y_center = int(y_center_norm * h_img)
            w_box = int(width_norm * w_img)
            h_box = int(height_norm * h_img)

            # Calcular esquinas (x1, y1) - (x2, y2)
            x1 = int(x_center - (w_box / 2))
            y1 = int(y_center - (h_box / 2))
            x2 = x1 + w_box
            y2 = y1 + h_box

            # Dibujar Rectángulo (Verde)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Dibujar Centro (Rojo)
            cv2.circle(img, (x_center, y_center), 3, (0, 0, 255), -1)
            
    return img

def main():
    images = load_images()
    
    if not images:
        print(f"No se encontraron imágenes en '{IMG_FOLDER}'")
        return

    index = len(images) - 1 # Empezar por la última (la más reciente)
    
    print("--- VISOR DE DATASET YOLO ---")
    print(f"-> Se encontraron {len(images)} imágenes.")
    print("-> Usa FLECHA IZQUIERDA / 'A' para anterior.")
    print("-> Usa FLECHA DERECHA / 'D' para siguiente.")
    print("-> Usa 'ESC' o 'Q' para salir.")

    while True:
        img_path = images[index]
        filename = os.path.basename(img_path)
        name_no_ext = os.path.splitext(filename)[0]
        label_path = os.path.join(LABEL_FOLDER, name_no_ext + ".txt")
        
        # 1. Cargar imagen
        img = cv2.imread(img_path)
        if img is None:
            print(f"Error cargando: {filename}")
            images.pop(index)
            if not images: break
            index = index % len(images)
            continue

        # 2. Dibujar etiquetas
        img = draw_yolo_labels(img, label_path)

        # 3. Información en pantalla
        info_text = f"[{index + 1}/{len(images)}] {filename}"
        cv2.rectangle(img, (0, 0), (w_img := img.shape[1], 30), (0, 0, 0), -1) # Fondo negro texto
        cv2.putText(img, info_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # 4. Mostrar
        cv2.imshow("Verificador YOLO", img)

        # 5. Esperar Tecla
        # waitKeyEx es mejor para flechas en Windows
        key = cv2.waitKeyEx(0) 
        
        # Códigos de teclas comunes
        # ESC=27, Q=113
        # Left Arrow: 2424832 (Win), 65361 (Linux), 81 (Some builds)
        # Right Arrow: 2555904 (Win), 65363 (Linux), 83 (Some builds)
        
        if key == 27 or key == ord('q'): # Salir
            break
        
        elif key in [2555904, 65363, 83, ord('d')]: # Derecha / Next
            index = (index + 1) % len(images)
            
        elif key in [2424832, 65361, 81, ord('a')]: # Izquierda / Prev
            index = (index - 1 + len(images)) % len(images)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()