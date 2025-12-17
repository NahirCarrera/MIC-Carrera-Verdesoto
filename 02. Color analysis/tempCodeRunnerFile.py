import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def analyze_ketchup_heatmap_overlay(folder_path):
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
        
        # 1. PRE-PROCESAMIENTO: Blur suave (Necesario para que el heatmap no tenga ruido)
        img_blur = cv2.GaussianBlur(img, (5, 5), 0)
        
        # 2. GENERACIÓN DE LA MATRIZ DE CALOR (R - G)
        # Esta es la "Verdad Absoluta" del mapa de calor.
        b, g, r = cv2.split(img_blur)
        diff_rg = cv2.subtract(r, g)
        norm_diff = cv2.normalize(diff_rg, None, 0, 255, cv2.NORM_MINMAX)
        
        # 3. EXTRACCIÓN DIRECTA (SIN FILTROS EXTRA)
        # En la escala de color JET:
        # 0-127: Tonos fríos (Fondo)
        # 128-255: Tonos cálidos (Objeto)
        # Usamos 128 como corte exacto.
        _, mask_raw = cv2.threshold(norm_diff, 150, 255, cv2.THRESH_BINARY)

        # 4. SOLO RELLENO DE HUECOS (SIN MODIFICAR BORDES)
        # El único problema del ketchup son los reflejos blancos puros (brillos de luz).
        # En el mapa de calor, esos brillos son agujeros negros/azules dentro del rojo.
        # Usamos CLOSE solo para tapar esos agujeros internos.
        # NO usamos Erode ni Dilate, para no mover el borde ni un milímetro.
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        mask_final = cv2.morphologyEx(mask_raw, cv2.MORPH_CLOSE, kernel_close, iterations=2)

        # Filtro de área (Solo para quitar ruido de cámara, no comida)
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask_final)
        
        for cnt in contours:
            if cv2.contourArea(cnt) > 20: 
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)

        # CÁLCULO
        food_pixels = cv2.countNonZero(mask_filtered)
        total_pixels = img.shape[0] * img.shape[1]
        percent = (food_pixels / total_pixels) * 100

        # VISUALIZACIÓN
        img_visual = img.copy()
        contours_vis, _ = cv2.findContours(mask_filtered, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        # Dibujamos en VERDE NEÓN
        # Usamos grosor 1 para que veas la precisión exacta
        cv2.drawContours(img_visual, contours_vis, -1, (0, 255, 0), 1)
        
        # Mapa de Calor (Generado idéntico a la máscara)
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
    plt.suptitle("Ketchup: Superposición Directa del Mapa de Calor", fontsize=16)

    for i in range(num_images):
        r = (i // cols); c = (i % cols)
        
        ax_img = fig.add_subplot(rows * 2, cols, (r * 2 * cols) + c + 1)
        data = results_data[i]
        ax_img.imshow(data['image'])
        ax_img.set_title(f"{data['name']}\n{data['percent']:.1f}%", fontsize=10, fontweight='bold')
        ax_img.axis('off')

        ax_heat = fig.add_subplot(rows * 2, cols, ((r * 2 + 1) * cols) + c + 1)
        ax_heat.imshow(data['heatmap'])
        ax_heat.set_title("Mapa de Calor (Fuente)", fontsize=9)
        ax_heat.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    folder = r"color_analysis\ketchup" 
    analyze_ketchup_heatmap_overlay(folder)