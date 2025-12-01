import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def analyze_onion_narrow_band(folder_path):
    if not os.path.exists(folder_path):
        print("Error: Carpeta no encontrada.")
        return

    files = sorted([f for f in os.listdir(folder_path) if f.endswith('.png')])
    if not files:
        print("No se encontraron imágenes PNG.")
        return

    results_data = []

    print(f"{'ARCHIVO':<30} | {'% FINAL':<10}")
    print("-" * 45)

    for filename in files:
        path = os.path.join(folder_path, filename)
        img = cv2.imread(path)
        if img is None: continue
        
        h_img, w_img = img.shape[:2]

        # 1. ATENUACIÓN (Mantenemos tu idea de bajar brillo)
        img_dimmed = cv2.convertScaleAbs(img, alpha=0.8, beta=0)
        gray = cv2.cvtColor(img_dimmed, cv2.COLOR_BGR2GRAY)

        # 2. FILTRO DE BANDA ESTRECHA (Solo lo Amarillo/Naranja)
        # - Límite Inferior: 145 (Elimina Verde/Cyan)
        # - Límite Superior: 170 (Elimina Rojo/Reflejos)
        mask_final = cv2.inRange(gray, 145, 170)

        # --- CÁLCULO ---
        food_pixels = cv2.countNonZero(mask_final)
        total_pixels = h_img * w_img
        percent = (food_pixels / total_pixels) * 100

        # --- VISUALIZACIÓN ---
        img_visual = img.copy()
        
        # Usamos RETR_TREE para ver huecos
        contours_full, _ = cv2.findContours(mask_final, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        for cnt in contours_full:
            if cv2.contourArea(cnt) > 0: 
                cv2.drawContours(img_visual, [cnt], -1, (0, 255, 0), 2)
        
        # Mapa de calor
        heatmap_view = cv2.applyColorMap(gray, cv2.COLORMAP_JET)

        # CORRECCIÓN: Limpiamos el nombre quitando '.png'
        state_name = filename.replace('.png', '')
        
        results_data.append({'name': state_name, 'percent': percent, 
                             'image': cv2.cvtColor(img_visual, cv2.COLOR_BGR2RGB), 
                             'heatmap': cv2.cvtColor(heatmap_view, cv2.COLOR_BGR2RGB)})
        
        # Imprimimos el nombre limpio
        print(f"{state_name:<30} | {percent:6.2f}%")

    # GRAFICAR
    if not results_data: return
    num_images = len(results_data)
    import math
    cols = 3
    rows = math.ceil(num_images / cols) 
    
    fig = plt.figure(figsize=(16, 5 * rows))
    plt.suptitle("Onion", fontsize=16)

    for i in range(num_images):
        r = (i // cols); c = (i % cols)
        
        ax_img = fig.add_subplot(rows * 2, cols, (r * 2 * cols) + c + 1)
        data = results_data[i]
        ax_img.imshow(data['image'])
        ax_img.set_title(f"{data['name']}\n{data['percent']:.1f}%", fontsize=10, fontweight='bold')
        ax_img.axis('off')

        ax_heat = fig.add_subplot(rows * 2, cols, ((r * 2 + 1) * cols) + c + 1)
        ax_heat.imshow(data['heatmap'])
        ax_heat.set_title("Mapa de Calor", fontsize=9)
        ax_heat.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    folder = r"color_analysis\onion" 
    analyze_onion_narrow_band(folder)