"""
test.py
=======
Prueba el modelo YOLO entrenado con imágenes individuales o el dataset de validación.

USO:
    # Probar con una imagen específica
    python test.py --model runs/auditai_xxx/weights/best.pt --image ruta/imagen.png

    # Probar con todo el dataset de validación
    python test.py --model runs/auditai_xxx/weights/best.pt --val

    # Probar con la cámara / captura de pantalla en vivo
    python test.py --model runs/auditai_xxx/weights/best.pt --live

    --conf 0.5     Umbral de confianza mínima (default: 0.25)
"""

import os
import sys
import argparse
import glob

# Mapeo de clases
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


def find_best_model():
    """Busca automáticamente el último best.pt en runs/."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    runs_dir = os.path.join(script_dir, "runs")
    
    if not os.path.exists(runs_dir):
        return None
    
    # Buscar todos los best.pt
    best_files = glob.glob(os.path.join(runs_dir, "**", "weights", "best.pt"), recursive=True)
    
    if not best_files:
        return None
    
    # Retornar el más reciente
    best_files.sort(key=os.path.getmtime, reverse=True)
    return best_files[0]


def test_single_image(model_path, image_path, conf=0.25):
    """Prueba el modelo con una imagen y muestra resultados."""
    from ultralytics import YOLO
    import cv2
    
    print(f"🔍 Analizando: {image_path}")
    
    model = YOLO(model_path)
    results = model(image_path, conf=conf, verbose=False)
    
    # Procesar resultados
    result = results[0]
    detections = result.boxes
    
    if len(detections) == 0:
        print("   ❌ No se detectaron objetos (imagen obstruida o vacía)")
    else:
        print(f"\n   {'Clase':<12} {'Confianza':>10} {'Coordenadas (x1,y1,x2,y2)'}")
        print(f"   {'─'*12} {'─'*10} {'─'*30}")
        
        for box in detections:
            cls_id = int(box.cls[0])
            conf_val = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_name = CLASS_MAP.get(cls_id, f"clase_{cls_id}")
            
            print(f"   {cls_name:<12} {conf_val:>9.2%}  [{x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f}]")
    
    # Mostrar imagen con detecciones
    annotated = result.plot()
    cv2.imshow("YOLO Detection - Press any key to close", annotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    return result


def test_validation(model_path, conf=0.25):
    """Evalúa el modelo en el dataset de validación completo."""
    from ultralytics import YOLO
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_yaml = os.path.join(script_dir, "data.yaml")
    
    if not os.path.exists(data_yaml):
        print("❌ No se encontró data.yaml")
        return
    
    print(f"📊 Evaluando modelo en dataset de validación...")
    
    model = YOLO(model_path)
    metrics = model.val(data=data_yaml, conf=conf, verbose=True)
    
    print(f"\n{'='*60}")
    print(f"  RESULTADOS DE VALIDACIÓN")
    print(f"{'='*60}")
    print(f"  mAP50:     {metrics.box.map50:.4f}")
    print(f"  mAP50-95:  {metrics.box.map:.4f}")
    print(f"{'='*60}\n")
    
    return metrics


def test_live(model_path, conf=0.25):
    """
    Modo en vivo: captura la pantalla en tiempo real y muestra detecciones.
    Usa las coordenadas de coordinates_config.json si existe.
    """
    from ultralytics import YOLO
    from PIL import ImageGrab
    import cv2
    import numpy as np
    import json
    import ctypes
    
    # Fix DPI
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # Cargar coordenadas
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    coord_file = os.path.join(project_root, "01. Labelling data", "coordinates_config.json")
    
    FIXED_LEFT = 1000
    FIXED_TOP = 224
    SCREEN_BOX_SIZE = 400
    
    if os.path.exists(coord_file):
        with open(coord_file, 'r') as f:
            data = json.load(f)
            FIXED_LEFT = data.get("FIXED_LEFT", FIXED_LEFT)
            FIXED_TOP = data.get("FIXED_TOP", FIXED_TOP)
            SCREEN_BOX_SIZE = data.get("SCREEN_BOX_SIZE", SCREEN_BOX_SIZE)
        print(f"📍 Coordenadas cargadas: ({FIXED_LEFT}, {FIXED_TOP}) size={SCREEN_BOX_SIZE}")
    
    print(f"\n🎥 MODO EN VIVO - Presiona 'Q' para salir")
    print(f"   Capturando área: ({FIXED_LEFT},{FIXED_TOP}) {SCREEN_BOX_SIZE}x{SCREEN_BOX_SIZE}")
    
    model = YOLO(model_path)
    
    while True:
        # Capturar pantalla
        bbox = (FIXED_LEFT, FIXED_TOP, FIXED_LEFT + SCREEN_BOX_SIZE, FIXED_TOP + SCREEN_BOX_SIZE)
        screen = ImageGrab.grab(bbox=bbox, all_screens=True)
        frame = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        
        # Detectar
        results = model(frame, conf=conf, verbose=False)
        annotated = results[0].plot()
        
        # Info en pantalla
        det_count = len(results[0].boxes)
        cv2.putText(annotated, f"Detecciones: {det_count}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Mostrar
        cv2.imshow("YOLO Live Detection - Press Q to quit", annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Prueba modelo YOLO entrenado")
    parser.add_argument("--model", type=str, default=None, help="Ruta al modelo .pt (si no se da, busca el último)")
    parser.add_argument("--image", type=str, default=None, help="Ruta a imagen para probar")
    parser.add_argument("--val", action="store_true", help="Evaluar en dataset de validación")
    parser.add_argument("--live", action="store_true", help="Modo en vivo (captura de pantalla)")
    parser.add_argument("--conf", type=float, default=0.25, help="Umbral de confianza (default: 0.25)")
    
    args = parser.parse_args()
    
    # Buscar modelo
    model_path = args.model
    if model_path is None:
        model_path = find_best_model()
        if model_path is None:
            print("❌ No se encontró ningún modelo entrenado.")
            print("   Entrena uno con: python train.py")
            print("   O especifica la ruta: python test.py --model ruta/best.pt")
            return
        print(f"🔍 Usando modelo más reciente: {model_path}")
    
    if not os.path.exists(model_path):
        print(f"❌ No se encontró el modelo: {model_path}")
        return
    
    # Verificar ultralytics
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ Instala ultralytics: pip install ultralytics")
        return
    
    print(f"\n{'='*60}")
    print(f"  TEST YOLO")
    print(f"{'='*60}")
    print(f"  Modelo:    {model_path}")
    print(f"  Confianza: {args.conf}")
    
    if args.val:
        test_validation(model_path, args.conf)
    elif args.live:
        test_live(model_path, args.conf)
    elif args.image:
        if not os.path.exists(args.image):
            print(f"❌ No se encontró la imagen: {args.image}")
            return
        test_single_image(model_path, args.image, args.conf)
    else:
        # Si no se da ninguna opción, mostrar opciones
        print(f"\n  Opciones:")
        print(f"    python test.py --image ruta/foto.png   (probar una imagen)")
        print(f"    python test.py --val                   (evaluar validación)")
        print(f"    python test.py --live                  (captura en vivo)")


if __name__ == "__main__":
    main()
