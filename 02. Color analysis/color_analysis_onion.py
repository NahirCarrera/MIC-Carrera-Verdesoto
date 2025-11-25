import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def analyze_onion_true_fidelity(folder_path):
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

        # 1. SUAVIZADO LIGERO
        blur = cv2.GaussianBlur(img, (3, 3), 0)

        # 2. LAB - CANAL B
        lab = cv2.cvtColor(blur, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # 3. UMBRAL FIEL (128)
        # Atrapa todo lo que no sea fondo azul puro.
        _, mask_heat = cv2.threshold(b, 130, 255, cv2.THRESH_BINARY)

        # 4. PROTECCIÓN CONTRA BRILLOS
        _, mask_glare = cv2.threshold(l, 250, 255, cv2.THRESH_BINARY)
        mask = cv2.subtract(mask_heat, mask_glare)

        # --- MARCO DE SEGURIDAD MÍNIMO ---
        # Solo 5px para evitar ruido del borde extremo de la cámara.
        h, w = mask.shape
        cv2.rectangle(mask, (0,0), (w, h), 0, thickness=5)

        # --- MORFOLOGÍA DE "FIDELIDAD" ---
        # NO USAMOS CLOSE NI DILATE para no tapar huecos.
        
        # Usamos OPEN suave (3x3) para separar islas que apenas se tocan.
        # Esto permite que se formen múltiples contornos separados.
        kernel_sep = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_sep, iterations=1)

        # 5. FILTRO DE ÁREA (CERO)
        # Si existe, se dibuja. Esto incluye migajas y huecos internos.
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        mask_final = np.zeros_like(mask)
        
        # Dibujamos todos los contornos (externos e internos/huecos)
        for i, cnt in enumerate(contours):
            if cv2.contourArea(cnt) > 0:
                # Usamos RETR_TREE y hierarchy para dibujar correctamente los huecos
                cv2.drawContours(mask_final, contours, i, 255, -1, hierarchy=hierarchy)
        mask = mask_final

        # CALCULAR
        food_pixels = cv2.countNonZero(mask)
        total_pixels = img.shape[0] * img.shape[1]
        percent = (food_pixels / total_pixels) * 100

        # VISUALIZAR
        img_visual = img.copy()
        # Volvemos a buscar para dibujar la línea verde final
        final_contours, final_hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # Grosor 1 para máxima precisión visual
        cv2.drawContours(img_visual, final_contours, -1, (0, 255, 0), 1, hierarchy=final_hierarchy)
        img_visual_rgb = cv2.cvtColor(img_visual, cv2.COLOR_BGR2RGB)

        # MAPA DE CALOR (Referencia visual)
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
    plt.suptitle("Detección Fiel (Islas y Huecos basados en Mapa de Calor)", fontsize=16)

    for i in range(num_images):
        r = (i // cols); c = (i % cols)
        ax_img = fig.add_subplot(rows * 2, cols, (r * 2 * cols) + c + 1)
        data = results_data[i]
        ax_img.imshow(data['image'])
        ax_img.set_title(f"{data['name']}\n{data['percent']:.1f}%", fontsize=12, fontweight='bold')
        ax_img.axis('off')

        ax_heat = fig.add_subplot(rows * 2, cols, ((r * 2 + 1) * cols) + c + 1)
        ax_heat.imshow(data['heatmap'])
        ax_heat.set_title("Mapa de Calor (Referencia)", fontsize=9)
        ax_heat.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    folder = "color_analysis/onion" 
    analyze_onion_true_fidelity(folder)