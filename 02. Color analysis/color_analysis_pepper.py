import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def analyze_peppers_lab(folder_path):
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
        # Un desenfoque medio ayuda a suavizar los brillos fuertes del pimiento
        img_blur = cv2.GaussianBlur(img, (5, 5), 0)

        # 2. CONVERSIÓN A LAB
        # Usamos LAB porque separa la Luminosidad (L) del Color (A y B).
        # Para el pimiento (Amarillo/Verde), el canal B es el más informativo.
        lab = cv2.cvtColor(img_blur, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # 3. UMBRALIZACIÓN EN CANAL B (AMARILLO)
        # El metal (gris) tiene un valor B cercano a 128 (neutro).
        # El pimiento tiene componente amarilla, así que su valor B será alto.
        # Probamos con 142 para cortar el metal sucio pero capturar el pimiento pálido.
        thresh_val = 147
        _, mask = cv2.threshold(b_channel, thresh_val, 255, cv2.THRESH_BINARY)

        # 4. MORFOLOGÍA (CRÍTICO PARA PIMIENTO)
        # El pimiento tiene "brillos blancos" (reflejos) que crean agujeros en la máscara.
        # Usamos MORPH_CLOSE para cerrar esos agujeros dentro de los trozos.
        kernel_close = np.ones((5,5), np.uint8) 
        mask_closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        
        # Un poco de Erode para separar trozos que apenas se tocan y limpiar ruido de fondo
        kernel_erode = np.ones((3,3), np.uint8)
        mask_final = cv2.erode(mask_closed, kernel_erode, iterations=1)

        # Filtro de área (Eliminar ruido pequeño)
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask_final)
        
        for cnt in contours:
            # Filtramos motas pequeñas (< 50px)
            if cv2.contourArea(cnt) > 50: 
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)

        # CÁLCULO
        food_pixels = cv2.countNonZero(mask_filtered)
        total_pixels = img.shape[0] * img.shape[1]
        percent = (food_pixels / total_pixels) * 100

        # VISUALIZACIÓN
        img_visual = img.copy()
        contours_vis, _ = cv2.findContours(mask_filtered, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(img_visual, contours_vis, -1, (0, 255, 0), 2)
        
        # Mapa de Calor: Usamos el Canal B (Intensidad Amarilla)
        # Esto nos mostrará qué tan "amarillo" ve el algoritmo cada zona
        heatmap_view = cv2.applyColorMap(b_channel, cv2.COLORMAP_JET)

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
    plt.suptitle("Pepper", fontsize=16)

    for i in range(num_images):
        r = (i // cols); c = (i % cols)
        
        ax_img = fig.add_subplot(rows * 2, cols, (r * 2 * cols) + c + 1)
        data = results_data[i]
        ax_img.imshow(data['image'])
        ax_img.set_title(f"{data['name']}\n{data['percent']:.1f}%", fontsize=10, fontweight='bold')
        ax_img.axis('off')

        ax_heat = fig.add_subplot(rows * 2, cols, ((r * 2 + 1) * cols) + c + 1)
        ax_heat.imshow(data['heatmap'])
        ax_heat.set_title("Intensidad Amarilla (Canal B)", fontsize=9)
        ax_heat.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Ajusta la ruta a tu carpeta de pimientos
    folder = r"color_analysis\pepper" 
    analyze_peppers_lab(folder)