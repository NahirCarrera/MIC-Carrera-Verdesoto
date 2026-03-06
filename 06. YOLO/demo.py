"""
demo.py
=======
Demo visual de predicciones YOLO sobre imágenes de prueba.

Lee todas las imágenes de la carpeta test_images/ y muestra:
  - Bounding boxes de cada bandeja detectada
  - Nombre del ingrediente + porcentaje de confianza sobre cada caja
  - Resumen en consola con tabla de confianza por imagen

USO:
    python demo.py
    python demo.py --model runs/auditai_xxx/weights/best.pt
    python demo.py --conf 0.3          # Confianza mínima
    python demo.py --save              # Guardar imágenes anotadas en test_images/results/
    python demo.py --no-show           # Solo guardar, no mostrar ventanas

CONTROLES (cuando se muestra la ventana):
    Cualquier tecla  →  Siguiente imagen
    Q                →  Salir
"""

import os
import sys
import glob
import argparse
import cv2
import numpy as np

# ─── Configuración de clases ─────────────────────────────────────────────────

CLASS_MAP = {
    0: "tomato",
    1: "lettuce",
    2: "onion",
    3: "pickles",
    4: "pepper",
    5: "bacon",
    6: "ketchup",
    7: "mayo",
    8: "jalapeno",
}

# Colores BGR para cada clase (visualmente distintos)
CLASS_COLORS = {
    0: (0, 0, 255),       # tomato    → rojo
    1: (0, 200, 0),       # lettuce   → verde
    2: (255, 200, 100),   # onion     → celeste
    3: (0, 180, 0),       # pickles   → verde oscuro
    4: (0, 140, 255),     # pepper    → naranja
    5: (50, 50, 200),     # bacon     → marrón
    6: (0, 0, 200),       # ketchup   → rojo oscuro
    7: (200, 230, 250),   # mayo      → crema
    8: (0, 200, 200),     # jalapeno  → amarillo
}


def find_best_model():
    """Busca automáticamente el mejor modelo entrenado en runs/."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    runs_dir = os.path.join(script_dir, "runs")

    if not os.path.exists(runs_dir):
        return None

    best_files = glob.glob(os.path.join(runs_dir, "**", "weights", "best.pt"), recursive=True)
    if not best_files:
        return None

    best_files.sort(key=os.path.getmtime, reverse=True)
    return best_files[0]


def draw_detections(image, detections):
    """
    Dibuja bounding boxes personalizados con nombre + confianza.
    Retorna la imagen anotada.
    """
    annotated = image.copy()
    h_img, w_img = annotated.shape[:2]

    for box in detections:
        cls_id = int(box.cls[0])
        conf_val = float(box.conf[0])
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]

        cls_name = CLASS_MAP.get(cls_id, f"clase_{cls_id}")
        color = CLASS_COLORS.get(cls_id, (200, 200, 200))

        # ── Bounding box ──
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        # ── Etiqueta: "ingrediente 95.2%" ──
        label = f"{cls_name} {conf_val:.1%}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        thickness = 2

        (tw, th), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        # Fondo del texto (arriba de la caja, o abajo si no cabe)
        label_y = y1 - 8
        if label_y - th - 4 < 0:
            label_y = y2 + th + 8

        rect_top = label_y - th - 4
        rect_bot = label_y + 4
        rect_left = x1
        rect_right = x1 + tw + 6

        # Fondo semi-transparente
        overlay = annotated.copy()
        cv2.rectangle(overlay, (rect_left, rect_top), (rect_right, rect_bot), color, -1)
        cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)

        # Texto
        cv2.putText(annotated, label, (x1 + 3, label_y), font, font_scale, (255, 255, 255), thickness)

    return annotated


def draw_summary_panel(image, detections, image_name):
    """
    Dibuja un panel lateral con el resumen de todas las detecciones.
    Muestra nombre del ingrediente + barra de confianza.
    """
    h_img, w_img = image.shape[:2]
    panel_w = 300
    panel = np.zeros((h_img, panel_w, 3), dtype=np.uint8)
    panel[:] = (30, 30, 30)  # fondo gris oscuro

    font = cv2.FONT_HERSHEY_SIMPLEX
    y_offset = 30

    # Título
    cv2.putText(panel, "DEMO YOLO - AuditAI", (10, y_offset), font, 0.6, (0, 200, 255), 2)
    y_offset += 30

    # Nombre de imagen
    short_name = os.path.basename(image_name)
    if len(short_name) > 30:
        short_name = short_name[:27] + "..."
    cv2.putText(panel, short_name, (10, y_offset), font, 0.4, (180, 180, 180), 1)
    y_offset += 30

    # Línea separadora
    cv2.line(panel, (10, y_offset), (panel_w - 10, y_offset), (80, 80, 80), 1)
    y_offset += 20

    if len(detections) == 0:
        cv2.putText(panel, "Sin detecciones", (10, y_offset), font, 0.5, (0, 0, 255), 1)
        cv2.putText(panel, "(imagen obstruida", (10, y_offset + 22), font, 0.4, (150, 150, 150), 1)
        cv2.putText(panel, " o sin bandejas)", (10, y_offset + 42), font, 0.4, (150, 150, 150), 1)
    else:
        # Encabezado
        cv2.putText(panel, f"{len(detections)} bandeja(s) detectada(s)", (10, y_offset), font, 0.5, (0, 255, 0), 1)
        y_offset += 30

        # Ordenar por confianza descendente
        det_list = []
        for box in detections:
            cls_id = int(box.cls[0])
            conf_val = float(box.conf[0])
            det_list.append((cls_id, conf_val))
        det_list.sort(key=lambda x: x[1], reverse=True)

        bar_max_w = 160  # ancho máximo de la barra

        for cls_id, conf_val in det_list:
            cls_name = CLASS_MAP.get(cls_id, f"clase_{cls_id}")
            color = CLASS_COLORS.get(cls_id, (200, 200, 200))

            # Nombre del ingrediente
            cv2.putText(panel, f"{cls_name}", (10, y_offset), font, 0.5, color, 1)

            # Porcentaje
            pct_text = f"{conf_val:.1%}"
            cv2.putText(panel, pct_text, (panel_w - 65, y_offset), font, 0.45, (220, 220, 220), 1)

            y_offset += 18

            # Barra de confianza
            bar_w = int(bar_max_w * conf_val)
            cv2.rectangle(panel, (10, y_offset - 2), (10 + bar_max_w, y_offset + 10), (60, 60, 60), -1)
            cv2.rectangle(panel, (10, y_offset - 2), (10 + bar_w, y_offset + 10), color, -1)

            y_offset += 24

            if y_offset > h_img - 40:
                cv2.putText(panel, "...", (10, y_offset), font, 0.5, (180, 180, 180), 1)
                break

    # Confianza promedio al final
    if len(detections) > 0:
        avg_conf = np.mean([float(box.conf[0]) for box in detections])
        y_bottom = h_img - 50
        cv2.line(panel, (10, y_bottom - 10), (panel_w - 10, y_bottom - 10), (80, 80, 80), 1)
        cv2.putText(panel, f"Confianza promedio:", (10, y_bottom + 10), font, 0.45, (180, 180, 180), 1)
        
        # Color según confianza
        if avg_conf >= 0.7:
            avg_color = (0, 255, 0)
        elif avg_conf >= 0.4:
            avg_color = (0, 200, 255)
        else:
            avg_color = (0, 0, 255)
        
        cv2.putText(panel, f"{avg_conf:.1%}", (200, y_bottom + 10), font, 0.55, avg_color, 2)

    # Instrucciones
    cv2.putText(panel, "Tecla: siguiente | Q: salir", (10, h_img - 12), font, 0.35, (120, 120, 120), 1)

    # Combinar imagen + panel
    combined = np.hstack([image, panel])
    return combined


def run_demo(model_path, conf=0.25, save=False, show=True):
    """Ejecuta la demo sobre todas las imágenes de test_images/."""
    from ultralytics import YOLO

    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(script_dir, "test_images")

    if not os.path.exists(test_dir):
        print("❌ No se encontró la carpeta test_images/")
        print("   Créala y coloca imágenes de prueba ahí.")
        return

    # Buscar imágenes
    extensions = ("*.png", "*.jpg", "*.jpeg", "*.bmp")
    image_files = []
    for ext in extensions:
        image_files.extend(glob.glob(os.path.join(test_dir, ext)))

    if not image_files:
        print("❌ No hay imágenes en test_images/")
        print("   Coloca capturas (.png/.jpg) en la carpeta test_images/")
        return

    image_files.sort()
    print(f"\n{'='*60}")
    print(f"  DEMO YOLO - AuditAI")
    print(f"{'='*60}")
    print(f"  Modelo:    {model_path}")
    print(f"  Confianza: {conf}")
    print(f"  Imágenes:  {len(image_files)}")
    if save:
        print(f"  Guardar:   test_images/results/")
    print(f"{'='*60}\n")

    # Cargar modelo
    model = YOLO(model_path)

    # Carpeta de resultados
    results_dir = None
    if save:
        results_dir = os.path.join(test_dir, "results")
        os.makedirs(results_dir, exist_ok=True)

    # ── Tabla resumen para consola ──
    print(f"  {'#':<4} {'Imagen':<35} {'Det':>4} {'Conf. prom':>11}  {'Detalle'}")
    print(f"  {'─'*4} {'─'*35} {'─'*4} {'─'*11}  {'─'*30}")

    total_detections = 0
    all_confs = []

    for idx, img_path in enumerate(image_files, 1):
        img_name = os.path.basename(img_path)

        # Leer imagen
        image = cv2.imread(img_path)
        if image is None:
            print(f"  {idx:<4} {img_name:<35}  ⚠️  No se pudo leer")
            continue

        # Inferencia
        results = model(image, conf=conf, verbose=False)
        detections = results[0].boxes
        det_count = len(detections)
        total_detections += det_count

        # Confianza promedio
        if det_count > 0:
            confs = [float(box.conf[0]) for box in detections]
            avg_conf = np.mean(confs)
            all_confs.extend(confs)

            # Detalle de clases detectadas
            classes_found = []
            for box in detections:
                cls_id = int(box.cls[0])
                c = float(box.conf[0])
                classes_found.append(f"{CLASS_MAP.get(cls_id, '?')}({c:.0%})")
            detail = ", ".join(classes_found)

            print(f"  {idx:<4} {img_name:<35} {det_count:>4} {avg_conf:>10.1%}  {detail}")
        else:
            print(f"  {idx:<4} {img_name:<35} {det_count:>4} {'  ---':>11}  (sin detecciones)")

        # Dibujar detecciones + panel
        annotated = draw_detections(image, detections)
        combined = draw_summary_panel(annotated, detections, img_name)

        # Guardar
        if save and results_dir:
            out_name = f"demo_{img_name}"
            out_path = os.path.join(results_dir, out_name)
            cv2.imwrite(out_path, combined)

        # Mostrar
        if show:
            # Redimensionar si es muy grande
            screen_h = 800
            ch, cw = combined.shape[:2]
            if ch > screen_h:
                scale = screen_h / ch
                combined = cv2.resize(combined, (int(cw * scale), screen_h))

            cv2.imshow("DEMO YOLO - AuditAI", combined)
            key = cv2.waitKey(0) & 0xFF
            if key == ord('q') or key == ord('Q'):
                print("\n  (Salida anticipada por el usuario)")
                break

    if show:
        cv2.destroyAllWindows()

    # ── Resumen final ──
    print(f"\n{'='*60}")
    print(f"  RESUMEN DEMO")
    print(f"{'='*60}")
    print(f"  Total imágenes analizadas:   {len(image_files)}")
    print(f"  Total detecciones:           {total_detections}")

    if all_confs:
        print(f"  Confianza promedio global:   {np.mean(all_confs):.1%}")
        print(f"  Confianza mínima:            {np.min(all_confs):.1%}")
        print(f"  Confianza máxima:            {np.max(all_confs):.1%}")
    else:
        print(f"  (No hubo detecciones)")

    if save and results_dir:
        saved = len(glob.glob(os.path.join(results_dir, "demo_*")))
        print(f"\n  💾 {saved} imágenes guardadas en: {results_dir}")

    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Demo visual de predicciones YOLO")
    parser.add_argument("--model", type=str, default=None,
                        help="Ruta al modelo .pt (si no se da, busca el más reciente)")
    parser.add_argument("--conf", type=float, default=0.25,
                        help="Umbral de confianza mínima (default: 0.25)")
    parser.add_argument("--save", action="store_true",
                        help="Guardar imágenes anotadas en test_images/results/")
    parser.add_argument("--no-show", action="store_true",
                        help="No mostrar ventanas (solo guardar si --save)")

    args = parser.parse_args()

    # Buscar modelo
    model_path = args.model
    if model_path is None:
        model_path = find_best_model()
        if model_path is None:
            print("❌ No se encontró ningún modelo entrenado.")
            print("   Entrena uno con: python train.py")
            print("   O especifica la ruta: python demo.py --model ruta/best.pt")
            return
        print(f"🔍 Usando modelo más reciente: {model_path}")

    if not os.path.exists(model_path):
        print(f"❌ No se encontró el modelo: {model_path}")
        return

    # Verificar dependencias
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ Instala ultralytics: pip install ultralytics")
        return

    show = not args.no_show
    if not show and not args.save:
        print("⚠️  Usaste --no-show sin --save. No hay nada que hacer.")
        print("   Agrega --save para guardar resultados.")
        return

    run_demo(model_path, conf=args.conf, save=args.save, show=show)


if __name__ == "__main__":
    main()
