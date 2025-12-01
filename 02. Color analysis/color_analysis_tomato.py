import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def analyze_tomato_strict(folder_path):
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
        
        # 1. PRE-PROCESAMIENTO: Mínimo Blur
        img_blur = cv2.GaussianBlur(img, (3, 3), 0)
        
        # 2. CÁLCULO ESPECTRAL (R - G)
        b, g, r = cv2.split(img_blur)
        diff_rg = cv2.subtract(r, g)
        
        # Normalizamos de 0 a 255
        norm_diff = cv2.normalize(diff_rg, None, 0, 255, cv2.NORM_MINMAX)
        
        # --- EL CAMBIO CRÍTICO: UMBRAL ALTO ---
        # Antes usábamos 50, lo cual dejaba pasar el "jugo" (zona cian del heatmap).
        # El mapa de calor JET se pone amarillo/rojo alrededor de 128.
        # Subimos a 120 para cortar el puente.
        strict_thresh = 120
        _, mask_spectral = cv2.threshold(norm_diff, strict_thresh, 255, cv2.THRESH_BINARY)

        # 3. FILTRO SATURACIÓN (Soporte)
        hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV)
        s_channel = hsv[:,:,1]
        _, mask_sat = cv2.threshold(s_channel, 60, 255, cv2.THRESH_BINARY)

        mask_combined = cv2.bitwise_and(mask_spectral, mask_sat)

        # 4. MORFOLOGÍA: SOLO LIMPIEZA, NO UNIÓN
        # Eliminamos el MORPH_CLOSE anterior porque unía las islas.
        # Usamos MORPH_OPEN para eliminar el ruido granulado que quede.
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        mask_final = cv2.morphologyEx(mask_combined, cv2.MORPH_OPEN, kernel, iterations=1)

        # Filtro de área
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask_final)
        
        for cnt in contours:
            # Filtramos cosas muy pequeñas
            if cv2.contourArea(cnt) > 30: 
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)

        # CÁLCULO
        food_pixels = cv2.countNonZero(mask_filtered)
        total_pixels = img.shape[0] * img.shape[1]
        percent = (food_pixels / total_pixels) * 100

        # VISUALIZACIÓN
        img_visual = img.copy()
        contours_vis, _ = cv2.findContours(mask_filtered, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # Dibujamos en Cyan
        cv2.drawContours(img_visual, contours_vis, -1, (255, 255, 0), 2)
        
        # Mapa de Calor
        heatmap_view = cv2.applyColorMap(norm_diff, cv2.COLORMAP_JET)

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
    plt.suptitle("Tomato", fontsize=16)

    for i in range(num_images):
        r = (i // cols); c = (i % cols)
        
        ax_img = fig.add_subplot(rows * 2, cols, (r * 2 * cols) + c + 1)
        data = results_data[i]
        ax_img.imshow(data['image'])
        ax_img.set_title(f"{data['name']}\n{data['percent']:.1f}%", fontsize=10, fontweight='bold')
        ax_img.axis('off')

        ax_heat = fig.add_subplot(rows * 2, cols, ((r * 2 + 1) * cols) + c + 1)
        ax_heat.imshow(data['heatmap'])
        ax_heat.set_title("Señal Roja (R - G)", fontsize=9)
        ax_heat.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    folder = r"color_analysis\tomato" 
    analyze_tomato_strict(folder)