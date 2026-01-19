import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def analizar_mayonesa_con_heatmap(folder_path):
    """
    Analiza el llenado de mayonesa y genera mapas de calor para visualizar
    la probabilidad de detección por cada píxel.
    """
    if not os.path.exists(folder_path):
        print(f"Error: No se encontró la carpeta {folder_path}")
        return

    files = sorted([f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg'))])
    print(f"{'ARCHIVO':<25} | {'LLENADO %':<12} | {'ESTADO':<15}")
    print("-" * 60)

    results_data = []

    for filename in files:
        img = cv2.imread(os.path.join(folder_path, filename))
        if img is None: continue
        
        # 1. PRE-PROCESAMIENTO
        img_blur = cv2.GaussianBlur(img, (7, 7), 0)
        lab = cv2.cvtColor(img_blur, cv2.COLOR_BGR2Lab)
        
        # 2. K-MEANS PARA ENCONTRAR LA MAYONESA
        # Aplanamos la imagen para el algoritmo
        pixel_values = lab.reshape((-1, 3)).astype(np.float32)
        K = 3 # Grupos: 1. Mayonesa, 2. Bandeja, 3. Fondo/Sombras
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixel_values, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Identificamos el cluster de la mayonesa (el de mayor luminosidad 'L')
        idx_mayo = np.argmax(centers[:, 0])
        centro_mayo = centers[idx_mayo]

        # 3. GENERACIÓN DEL MAPA DE CALOR (Distancia Euclidiana)
        # Calculamos qué tan lejos está cada píxel del color "ideal" de la mayonesa
        distancias = np.linalg.norm(lab - centro_mayo, axis=2)
        
        # Normalizamos la distancia para que el color más cercano sea 255 (rojo) y el más lejano 0
        dist_norm = cv2.normalize(distancias, None, 0, 255, cv2.NORM_MINMAX)
        heatmap_gray = 255 - dist_norm.astype(np.uint8) # Invertimos para que mayo = brillante
        heatmap_color = cv2.applyColorMap(heatmap_gray, cv2.COLORMAP_JET)

        # 4. SEGMENTACIÓN FINAL
        labels = labels.reshape(lab.shape[:2])
        mask_sauce = np.zeros_like(labels, dtype=np.uint8)
        mask_sauce[labels == idx_mayo] = 255

        # Definición de área de bandeja (Denominador)
        gray = cv2.cvtColor(img_blur, cv2.COLOR_BGR2GRAY)
        _, mask_tray = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY)
        mask_tray = cv2.morphologyEx(mask_tray, cv2.MORPH_CLOSE, np.ones((15,15), np.uint8))

        # Filtro: Solo lo que esté dentro de la bandeja y sea del cluster correcto
        mask_sauce = cv2.bitwise_and(mask_sauce, mask_tray)
        mask_sauce = cv2.morphologyEx(mask_sauce, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))

        # 5. CÁLCULOS
        px_tray = cv2.countNonZero(mask_tray)
        px_sauce = cv2.countNonZero(mask_sauce)
        percent = (px_sauce / px_tray * 100) if px_tray > 0 else 0
        status = "NORMAL" if percent > 15 else "BAJO LLENADO"

        print(f"{filename:<25} | {percent:>10.2f}% | {status:<15}")

        # Guardar para visualización
        vis = img.copy()
        draw_contours(vis, mask_tray, (255, 0, 0), 2)
        draw_contours(vis, mask_sauce, (0, 255, 0), 2)
        
        results_data.append({
            'name': filename,
            'original': cv2.cvtColor(vis, cv2.COLOR_BGR2RGB),
            'heatmap': cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB),
            'perc': f"{percent:.2f}%"
        })

    display_results_thesis(results_data)

def draw_contours(img, mask, color, thickness):
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(img, cnts, -1, color, thickness)

def display_results_thesis(results):
    n = len(results)
    if n == 0: return
    fig, axes = plt.subplots(2, n, figsize=(4 * n, 8))
    if n == 1: axes = np.expand_dims(axes, axis=1)
    
    for i, r in enumerate(results):
        # Fila 1: Detección Original
        axes[0, i].imshow(r['original'])
        axes[0, i].set_title(f"{r['name']}\nLlenado: {r['perc']}")
        axes[0, i].axis('off')
        
        # Fila 2: Mapa de Calor
        axes[1, i].imshow(r['heatmap'])
        axes[1, i].set_title(f"Mapa de Calor (Probabilidad)")
        axes[1, i].axis('off')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    path = r"02. Color analysis\color_analysis\mayo"    
    analizar_mayonesa_con_heatmap(path)