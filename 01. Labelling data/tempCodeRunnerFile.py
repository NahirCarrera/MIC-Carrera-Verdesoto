import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def analyze_onion_balanced_raw(folder_path):
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

        # 1. SUAVIZADO
        blur = cv2.GaussianBlur(img, (5, 5), 0)

        # 2. LAB - CANAL B
        lab = cv2.cvtColor(blur, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # --- AJUSTE 1: EL PUNTO MEDIO ---
        # 130 detecta la bandeja. 132 pierde la migaja.
        # Usamos 131. Es el límite matemático.
        _, mask_yellow = cv2.threshold(b, 131, 255, cv2.THRESH_BINARY)

        # --- AJUSTE 2: ANTI-BRILLO AGRESIVO ---
        # Bajamos a 240. Esto elimina las paredes metálicas brillantes 
        # que causaron el problema del 100% en Medium.
        _, mask_glare = cv2.threshold(l, 240, 255, cv2.THRESH_BINARY)
        mask = cv2.subtract(mask_yellow, mask_glare)

        # 3. MORFOLOGÍA CRUDA (Para no perder la migaja)
        # No usamos OPEN (borrar). Solo usamos DILATE (unir).
        # Esto permite que sobrevivan los píxeles sueltos del Empty.
        kernel_connect = np.ones((3,3), np.uint8)
        mask = cv2.dilate(mask, kernel_connect, iterations=2) 
        
        # Cierre suave para rellenar huecos internos de la cebolla grande
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7,7), np.uint8))

        # 4. FILTRO DE ÁREA MÍNIMO
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mask_final = np.zeros_like(mask)
        
        for cnt in contours:
            # Filtro mínimo (> 10px) solo para quitar ruido digital invisible
            if cv2.contourArea(cnt) > 10: 
                cv2.drawContours(mask_final, [cnt], -1, 255, -1)
        mask = mask_final

        # CALCULAR
        food_pixels = cv2.countNonZero(mask)
        total_pixels = img.shape[0] * img.shape[1]
        percent = (food_pixels / total_pixels) * 100

        # VISUALIZAR
        img_visual = img.copy()
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Dibujamos en verde neón
        cv2.drawContours(img_visual, contours, -1, (0, 255, 0), 2)
        img_visual_rgb = cv2.cvtColor(img_visual, cv2.COLOR_BGR2RGB)

        # Mapa de Calor (SIN NORMALIZAR para ver la realidad)
        # Truco: Normalizamos MANUALMENTE con límites fijos para no engañarnos.
        # Así veremos si la migaja es realmente roja o solo gris claro.
        heatmap = np.zeros_like(b)
        # Mapeamos el rango crítico 128-140 a visible
        heatmap = cv2.normalize(b, None, 0, 255, cv2.NORM_MINMAX) 
        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
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
    plt.suptitle("Detección Equilibrada (Umbral 131 + Anti-Brillo)", fontsize=16)

    for i in range(num_images):
        r = (i // cols); c = (i % cols)
        ax_img = fig.add_subplot(rows * 2, cols, (r * 2 * cols) + c + 1)
        data = results_data[i]
        ax_img.imshow(data['image'])
        ax_img.set_title(f"{data['name']}\n{data['percent']:.1f}%", fontsize=12, fontweight='bold')
        ax_img.axis('off')

        ax_heat = fig.add_subplot(rows * 2, cols, ((r * 2 + 1) * cols) + c + 1)
        ax_heat.imshow(data['heatmap'])
        ax_heat.set_title("Calidez (Canal B)", fontsize=9)
        ax_heat.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    folder = "color_analysis/onion" 
    analyze_onion_balanced_raw(folder)