import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def analyze_yellow_range(folder_path):
    if not os.path.exists(folder_path):
        print("Error: Carpeta no encontrada.")
        return

    files = sorted([f for f in os.listdir(folder_path) if f.endswith('.png')])
    results_data = []

    print(f"{'ARCHIVO':<25} | {'% OCUPACIÓN':<15}")
    print("-" * 45)

    for filename in files:
        path = os.path.join(folder_path, filename)
        img = cv2.imread(path)
        if img is None: continue

        # 1. SEPARAR Y RESTAR
        b, g, r = cv2.split(img)
        diff_rg = cv2.subtract(r, g)

        # 2. AMPLIFICACIÓN (Normalización)
        # Esto estira el contraste para que lo tenue se vuelva visible
        norm_diff = cv2.normalize(diff_rg, None, 0, 255, cv2.NORM_MINMAX)

        # --- EL CAMBIO CLAVE: BAJAMOS EL UMBRAL ---
        # 135 (Rojo + Todo el Amarillo). 
        # Nota: Si ves que empieza a marcar el fondo azul, sube esto a 145.
        _, mask = cv2.threshold(norm_diff, 135, 255, cv2.THRESH_BINARY)

        # 3. RECUPERAR LO QUEMADO (Oscuridad)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask_dark = cv2.inRange(hsv, np.array([0, 20, 0]), np.array([180, 255, 60]))
        mask = cv2.bitwise_or(mask, mask_dark)

        # 4. MORFOLOGÍA (Conectar zonas amarillas con rojas)
        # Usamos un kernel mediano para fusionar el amarillo periférico con el rojo central
        kernel_connect = np.ones((7,7), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_connect)
        
        # Limpieza suave de bordes
        kernel_clean = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_clean)
        
        # Dilatación suave para suavizar el contorno final
        mask = cv2.dilate(mask, kernel_clean, iterations=1)

        # Filtro de Área
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask_final = np.zeros_like(mask)
        for cnt in contours:
            if cv2.contourArea(cnt) > 400: 
                cv2.drawContours(mask_final, [cnt], -1, 255, -1)
        mask = mask_final

        # CALCULAR
        food_pixels = cv2.countNonZero(mask)
        total_pixels = img.shape[0] * img.shape[1]
        percent = (food_pixels / total_pixels) * 100

        # VISUALIZAR
        img_visual = img.copy()
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(img_visual, contours, -1, (0, 255, 0), 2)
        img_visual_rgb = cv2.cvtColor(img_visual, cv2.COLOR_BGR2RGB)

        heatmap = cv2.applyColorMap(norm_diff, cv2.COLORMAP_JET)
        heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

        state_name = filename.split('.')[1].replace('_', ' ').title().strip()
        results_data.append({'name': state_name, 'percent': percent, 'image': img_visual_rgb, 'heatmap': heatmap_rgb})
        print(f"{filename:<25} | {percent:6.2f}%")

    # GRAFICAR
    if not results_data: return
    num_images = len(results_data)
    import math
    cols = 3
    rows = math.ceil(num_images / cols) 
    fig = plt.figure(figsize=(16, 5 * rows))
    plt.suptitle("Detección Ampliada", fontsize=16)
    for i in range(num_images):
        r = (i // cols); c = (i % cols)
        ax_img = fig.add_subplot(rows * 2, cols, (r * 2 * cols) + c + 1)
        data = results_data[i]
        ax_img.imshow(data['image'])
        ax_img.set_title(f"{data['name']}\n{data['percent']:.1f}%", fontsize=12, fontweight='bold')
        ax_img.axis('off')
        ax_heat = fig.add_subplot(rows * 2, cols, ((r * 2 + 1) * cols) + c + 1)
        ax_heat.imshow(data['heatmap'])
        ax_heat.set_title("Señal Amplificada", fontsize=9)
        ax_heat.axis('off')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    folder = "color_analysis/bacon" 
    analyze_yellow_range(folder)