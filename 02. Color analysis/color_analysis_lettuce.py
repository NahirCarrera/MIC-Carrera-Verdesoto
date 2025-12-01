import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def analyze_lettuce_exg_red_focus(folder_path):
    if not os.path.exists(folder_path):
        print("Error: Carpeta no encontrada.")
        return

    files = sorted([f for f in os.listdir(folder_path) if f.endswith('.png')])
    results_data = []

    print(f"{'ARCHIVO':<25} | {'% FINAL':<10}")
    print("-" * 40)

    for filename in files:
        path = os.path.join(folder_path, filename)
        img = cv2.imread(path)
        if img is None: continue
        
        # Trabajamos con floats para evitar desbordamientos en la resta
        img_float = img.astype(np.float32)
        
        # Separamos canales
        b, g, r = cv2.split(img_float)

        # --- CÁLCULO CIENTÍFICO: EXCESS GREEN INDEX (ExG) ---
        # (SEÑAL INTACTA, tal como la pediste)
        exg = 2 * g - r - b

        # Normalizamos el resultado a 0-255 para hacerlo imagen (MINMAX)
        # Esto hace que el valor más alto de CADA foto sea 255 (Rojo Puro)
        exg_norm = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX)
        exg_norm = exg_norm.astype(np.uint8)

        # --- UMBRALIZACIÓN (AQUÍ ESTÁ EL CAMBIO) ---
        # Antes estaba en 40 (tomaba azul/verde).
        # Lo subimos a 190 para que solo tome la zona ROJA/NARANJA del mapa de calor.
        _, mask = cv2.threshold(exg_norm, 150, 255, cv2.THRESH_BINARY)

        # --- LIMPIEZA DE RUIDO ---
        kernel_clean = np.ones((3,3), np.uint8)
        mask_clean = cv2.erode(mask, kernel_clean, iterations=1)
        
        # DILATE suave
        mask_final = cv2.dilate(mask_clean, kernel_clean, iterations=1)

        # Filtro de área final
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask_final)
        
        for cnt in contours:
            if cv2.contourArea(cnt) > 30: 
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)

        # CÁLCULO
        food_pixels = cv2.countNonZero(mask_filtered)
        total_pixels = img.shape[0] * img.shape[1]
        percent = (food_pixels / total_pixels) * 100

        # VISUALIZACIÓN
        img_visual = img.copy()
        contours_vis, _ = cv2.findContours(mask_filtered, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # Dibujamos en verde neón
        cv2.drawContours(img_visual, contours_vis, -1, (0, 255, 0), 2)
        
        # Visualizamos el mapa ExG en falso color
        heatmap_view = cv2.applyColorMap(exg_norm, cv2.COLORMAP_JET)

        state_name = filename.replace('.png', '')
        results_data.append({
            'name': state_name, 
            'percent': percent, 
            'image': cv2.cvtColor(img_visual, cv2.COLOR_BGR2RGB), 
            'heatmap': cv2.cvtColor(heatmap_view, cv2.COLOR_BGR2RGB)
        })
        
        print(f"{state_name:<25} | {percent:6.2f}%")

    # GRAFICAR
    if not results_data: return
    num_images = len(results_data)
    import math
    cols = 3
    rows = math.ceil(num_images / cols) 
    
    fig = plt.figure(figsize=(16, 5 * rows))
    plt.suptitle("Lettuce", fontsize=16)

    for i in range(num_images):
        r = (i // cols); c = (i % cols)
        
        ax_img = fig.add_subplot(rows * 2, cols, (r * 2 * cols) + c + 1)
        data = results_data[i]
        ax_img.imshow(data['image'])
        ax_img.set_title(f"{data['name']}\n{data['percent']:.1f}%", fontsize=10, fontweight='bold')
        ax_img.axis('off')

        ax_heat = fig.add_subplot(rows * 2, cols, ((r * 2 + 1) * cols) + c + 1)
        ax_heat.imshow(data['heatmap'])
        ax_heat.set_title("Mapa ExG", fontsize=9)
        ax_heat.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    folder = r"color_analysis\lettuce" 
    analyze_lettuce_exg_red_focus(folder)