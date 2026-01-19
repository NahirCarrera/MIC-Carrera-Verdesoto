import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def analizar_llenado_ketchup_con_heatmap(folder_path):
    """
    Analiza el llenado de ketchup agregando mapas de calor basados en la 
    intensidad de la respuesta cromática (R-G).
    """
    if not os.path.exists(folder_path):
        print(f"Error: No se encontró la carpeta {folder_path}")
        return

    files = sorted([f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg'))])
    print(f"{'ARCHIVO':<25} | {'SALSA %':<12} | {'ESTADO':<15}")
    print("-" * 60)

    results_data = []

    for filename in files:
        img = cv2.imread(os.path.join(folder_path, filename))
        if img is None: continue
        
        # 1. PRE-PROCESAMIENTO
        img_blur = cv2.medianBlur(img, 7)
        
        # 2. SEGMENTACIÓN DE BANDEJA (Denominador)
        gray = cv2.cvtColor(img_blur, cv2.COLOR_BGR2GRAY)
        _, mask_tray = cv2.threshold(gray, 35, 255, cv2.THRESH_BINARY)
        mask_tray = cv2.morphologyEx(mask_tray, cv2.MORPH_CLOSE, np.ones((11,11), np.uint8))

        # 3. GENERACIÓN DE MAPA DE CALOR (Diferencia R - G)
        b, g, r = cv2.split(img_blur.astype(np.float32))
        diff_rg = r - g
        
        # Normalizamos la diferencia para crear el mapa de calor
        # Solo consideramos valores positivos (donde el rojo domina)
        diff_rg_clipped = np.clip(diff_rg, 0, 255)
        heatmap_gray = cv2.normalize(diff_rg_clipped, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Aplicamos máscara de bandeja al heatmap para limpiar el fondo
        heatmap_gray = cv2.bitwise_and(heatmap_gray, mask_tray)
        heatmap_color = cv2.applyColorMap(heatmap_gray, cv2.COLORMAP_JET)

        # 4. SEGMENTACIÓN DE SALSA (Binaria)
        _, mask_sauce = cv2.threshold(diff_rg, 18, 255, cv2.THRESH_BINARY)
        mask_sauce = mask_sauce.astype(np.uint8)
        mask_sauce = cv2.bitwise_and(mask_sauce, mask_tray)

        # 5. CÁLCULOS
        px_total_tray = cv2.countNonZero(mask_tray)
        px_sauce = cv2.countNonZero(mask_sauce)
        sauce_percent = (px_sauce / px_total_tray * 100) if px_total_tray > 0 else 0
        status_msg = "NORMAL" if sauce_percent > 15 else "BAJO LLENADO"

        print(f"{filename:<25} | {sauce_percent:>10.2f}% | {status_msg:<15}")

        # VISUALIZACIÓN
        vis = img.copy()
        draw_contours(vis, mask_tray, (255, 0, 0), 1) # Azul: Tray
        draw_contours(vis, mask_sauce, (0, 255, 0), 1) # Verde: Sauce
        
        results_data.append({
            'name': filename,
            'original': cv2.cvtColor(vis, cv2.COLOR_BGR2RGB),
            'heatmap': cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB),
            'perc': f"{sauce_percent:.2f}%"
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
        # Fila 1: Imagen Procesada (Original + Contornos)
        axes[0, i].imshow(r['original'])
        axes[0, i].set_title(f"{r['name']}\nKetchup: {r['perc']}")
        axes[0, i].axis('off')
        
        # Fila 2: Mapa de Calor
        axes[1, i].imshow(r['heatmap'])
        axes[1, i].axis('off')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    path = r"02. Color analysis\color_analysis\ketchup" 
    analizar_llenado_ketchup_con_heatmap(path)