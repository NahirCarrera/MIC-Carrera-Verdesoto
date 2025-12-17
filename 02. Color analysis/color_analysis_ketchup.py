import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def analyze_ketchup_warm_saturation(folder_path):
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
        img_blur = cv2.GaussianBlur(img, (5, 5), 0)
        
        # 2. EXTRACTOR 1: CALIDEZ (Canal A del espacio LAB)
        # Esto mide qué tan "Rojo" es el objeto frente al Verde.
        lab = cv2.cvtColor(img_blur, cv2.COLOR_BGR2LAB)
        _, a_channel, _ = cv2.split(lab)
        
        # 3. EXTRACTOR 2: SATURACIÓN (Canal S del espacio HSV)
        # Esto mide qué tan "Vivo" es el color frente al Gris.
        hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV)
        s_channel = hsv[:,:,1]

        # 4. FUSIÓN DE SENSORES (PROMEDIO PONDERADO)
        # Combinamos ambos mundos. 
        # Le damos el mismo peso (0.5 y 0.5) a la Calidez y a la Saturación.
        # Resultado: Una imagen que brilla SOLO donde hay "Rojo Intenso".
        combined = cv2.addWeighted(a_channel, 0.5, s_channel, 0.5, 0)
        
        # Normalizamos para tener un mapa de calor perfecto de 0 a 255
        heatmap_raw = cv2.normalize(combined, None, 0, 255, cv2.NORM_MINMAX)

        # 5. UMBRAL DE CORTE (LA DEFINICIÓN)
        # Al sumar saturación, el fondo se vuelve muy oscuro (valores bajos).
        # El Ketchup brilla mucho.
        # Un corte en 115 separa perfectamente la salsa del metal.
        _, mask_raw = cv2.threshold(heatmap_raw, 150, 255, cv2.THRESH_BINARY)

        # 6. MORFOLOGÍA MÍNIMA (SOLO BRILLOS)
        # Solo tapamos los puntos blancos de luz.
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        mask_final = cv2.morphologyEx(mask_raw, cv2.MORPH_CLOSE, kernel_close, iterations=2)

        # Filtro de área
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
        
        # Dibujamos en VERDE NEÓN
        cv2.drawContours(img_visual, contours_vis, -1, (0, 255, 0), 1)
        
        # Mapa de Calor: Usamos la FUSIÓN (Calidez + Saturación)
        heatmap_view = cv2.applyColorMap(heatmap_raw, cv2.COLORMAP_JET)

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
    plt.suptitle("Ketchup: Fusión de Calidez (Lab-A) + Saturación (HSV-S)", fontsize=16)

    for i in range(num_images):
        r = (i // cols); c = (i % cols)
        
        ax_img = fig.add_subplot(rows * 2, cols, (r * 2 * cols) + c + 1)
        data = results_data[i]
        ax_img.imshow(data['image'])
        ax_img.set_title(f"{data['name']}\n{data['percent']:.1f}%", fontsize=10, fontweight='bold')
        ax_img.axis('off')

        ax_heat = fig.add_subplot(rows * 2, cols, ((r * 2 + 1) * cols) + c + 1)
        ax_heat.imshow(data['heatmap'])
        ax_heat.set_title("Señal Combinada", fontsize=9)
        ax_heat.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    folder = r"color_analysis\ketchup" 
    analyze_ketchup_warm_saturation(folder)