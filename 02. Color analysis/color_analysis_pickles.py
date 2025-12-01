import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def analyze_pickles_refined(folder_path):
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
        
        # 1. PRE-PROCESAMIENTO
        img_blur = cv2.GaussianBlur(img, (3, 3), 0) # Blur más suave para no perder bordes
        
        # --- ESTRATEGIA HÍBRIDA: ExG + SATURACIÓN ---
        
        # A) MÁSCARA ExG (Para detectar el color Verde Oliva)
        img_float = img_blur.astype(np.float32)
        b, g, r = cv2.split(img_float)
        exg = 2 * g - r - b
        exg_norm = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Subimos el umbral a 135 para ser más selectivos con el "verde sólido"
        _, mask_exg = cv2.threshold(exg_norm, 110, 255, cv2.THRESH_BINARY)

        # B) MÁSCARA DE SATURACIÓN (Para ignorar el metal húmedo/jugo)
        # El metal y el agua tienen baja saturación. El pepinillo es sólido.
        hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV)
        s_channel = hsv[:,:,1]
        
        # Umbral de saturación: Solo aceptamos colores "vivos" (> 40)
        _, mask_sat = cv2.threshold(s_channel, 40, 255, cv2.THRESH_BINARY)

        # COMBINACIÓN: Debe ser Verde (ExG) Y Sólido (Saturación)
        mask_combined = cv2.bitwise_and(mask_exg, mask_sat)

        # 4. MORFOLOGÍA DE PRECISIÓN (El cambio más importante)
        # Bajamos el kernel de (7,7) a (3,3) y las iteraciones a 1.
        # Queremos rellenar los huecos DENTRO de la rodaja (semillas), 
        # pero NO conectar rodajas separadas.
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        mask_closed = cv2.morphologyEx(mask_combined, cv2.MORPH_CLOSE, kernel_small, iterations=1)
        
        # Limpieza final de ruido
        mask_final = cv2.erode(mask_closed, kernel_small, iterations=1)

        # Filtro de área
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask_final)
        
        for cnt in contours:
            # Filtramos trozos muy pequeños
            if cv2.contourArea(cnt) > 30: 
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)

        # CÁLCULO
        food_pixels = cv2.countNonZero(mask_filtered)
        total_pixels = img.shape[0] * img.shape[1]
        percent = (food_pixels / total_pixels) * 100

        # VISUALIZACIÓN
        img_visual = img.copy()
        contours_vis, _ = cv2.findContours(mask_filtered, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # Dibujamos en Cyan para diferenciar
        cv2.drawContours(img_visual, contours_vis, -1, (0, 255, 0), 2)
        
        # Mapa de Calor (Mostramos ExG puro para referencia)
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
    plt.suptitle("Pickles", fontsize=16)

    for i in range(num_images):
        r = (i // cols); c = (i % cols)
        
        ax_img = fig.add_subplot(rows * 2, cols, (r * 2 * cols) + c + 1)
        data = results_data[i]
        ax_img.imshow(data['image'])
        ax_img.set_title(f"{data['name']}\n{data['percent']:.1f}%", fontsize=10, fontweight='bold')
        ax_img.axis('off')

        ax_heat = fig.add_subplot(rows * 2, cols, ((r * 2 + 1) * cols) + c + 1)
        ax_heat.imshow(data['heatmap'])
        ax_heat.set_title("Señal ExG", fontsize=9)
        ax_heat.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    folder = r"color_analysis\pickles" 
    analyze_pickles_refined(folder)