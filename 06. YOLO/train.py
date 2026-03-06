"""
train.py
========
Entrena un modelo YOLOv8 usando el dataset preparado por prepare_dataset.py.

REQUISITOS:
    pip install ultralytics

USO:
    python train.py

    --model yolov8n.pt     Modelo base (n=nano, s=small, m=medium, l=large, x=extra)
    --epochs 100           Número de épocas de entrenamiento
    --batch 16             Tamaño del batch (reduce si te quedas sin VRAM)
    --imgsz 640            Tamaño de imagen (debe coincidir con OUTPUT_SIZE de screenshoot.py)
    --device ''            Dispositivo: '' (auto), 'cpu', '0' (GPU 0), '0,1' (multi-GPU)
    --resume               Reanudar entrenamiento desde el último checkpoint
"""

import os
import argparse
from datetime import datetime

def check_dataset():
    """Verifica que el dataset exista antes de entrenar."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_dir = os.path.join(script_dir, "dataset")
    train_imgs = os.path.join(dataset_dir, "train", "images")
    val_imgs = os.path.join(dataset_dir, "val", "images")
    
    if not os.path.exists(train_imgs):
        print("❌ No se encontró dataset/train/images/")
        print("   Ejecuta primero: python prepare_dataset.py")
        return False
    
    if not os.path.exists(val_imgs):
        print("❌ No se encontró dataset/val/images/")
        print("   Ejecuta primero: python prepare_dataset.py")
        return False
    
    train_count = len([f for f in os.listdir(train_imgs) if f.endswith(('.png', '.jpg'))])
    val_count = len([f for f in os.listdir(val_imgs) if f.endswith(('.png', '.jpg'))])
    
    print(f"📊 Dataset encontrado: {train_count} train / {val_count} val")
    
    if train_count < 10:
        print("⚠️  Muy pocas imágenes de entrenamiento. Recomendado: >100")
    
    return True


def train(model_name="yolov8n.pt", epochs=100, batch=16, imgsz=640, device='', resume=False):
    """
    Entrena YOLO con el dataset preparado.
    """
    print("=" * 60)
    print("  ENTRENAMIENTO YOLO")
    print("=" * 60)
    
    # 1. Verificar dataset
    if not check_dataset():
        return
    
    # 2. Importar ultralytics (aquí para dar error claro si no está instalado)
    try:
        from ultralytics import YOLO
    except ImportError:
        print("\n❌ No se encontró la librería 'ultralytics'.")
        print("   Instálala con: pip install ultralytics")
        return
    
    # 3. Configuración
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_yaml = os.path.join(script_dir, "data.yaml")
    
    if not os.path.exists(data_yaml):
        print(f"❌ No se encontró {data_yaml}")
        return
    
    # Nombre único para esta sesión de entrenamiento
    run_name = f"auditai_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"\n⚙️  CONFIGURACIÓN:")
    print(f"   Modelo base:   {model_name}")
    print(f"   Épocas:        {epochs}")
    print(f"   Batch size:    {batch}")
    print(f"   Imagen size:   {imgsz}x{imgsz}")
    print(f"   Dispositivo:   {'auto' if device == '' else device}")
    print(f"   Data config:   {data_yaml}")
    print(f"   Run name:      {run_name}")
    print(f"   Resume:        {resume}")
    
    # 4. Cargar modelo
    print(f"\n🔄 Cargando modelo {model_name}...")
    
    if resume:
        # Buscar el último checkpoint
        last_pt = os.path.join(script_dir, "runs", "detect", "train", "weights", "last.pt")
        if os.path.exists(last_pt):
            model = YOLO(last_pt)
            print(f"   Reanudando desde: {last_pt}")
        else:
            print(f"   ⚠️  No se encontró checkpoint. Empezando desde cero con {model_name}")
            model = YOLO(model_name)
    else:
        model = YOLO(model_name)
    
    # 5. Entrenar
    print(f"\n🚀 Iniciando entrenamiento...")
    print(f"{'─'*60}\n")
    
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device if device else None,
        name=run_name,
        project=os.path.join(script_dir, "runs"),
        
        # Augmentation (YOLO ya aplica augmentation por defecto, estos son ajustes)
        hsv_h=0.015,      # Variación de Hue
        hsv_s=0.7,        # Variación de Saturación
        hsv_v=0.4,        # Variación de Valor
        degrees=0.0,      # No rotar (las bandejas siempre están horizontal)
        translate=0.1,     # Pequeña traslación
        scale=0.5,        # Escala
        fliplr=0.5,       # Flip horizontal
        flipud=0.0,       # No flip vertical (las bandejas no se ven al revés)
        mosaic=1.0,       # Mosaic augmentation
        
        # Paciencia para early stopping
        patience=20,
        
        # Guardar checkpoints
        save=True,
        save_period=10,    # Guardar cada 10 épocas
        
        # Verbose
        verbose=True,
    )
    
    # 6. Resultados
    print(f"\n{'='*60}")
    print(f"  ✅ ENTRENAMIENTO COMPLETADO")
    print(f"{'='*60}")
    
    # Buscar el mejor modelo
    run_dir = os.path.join(script_dir, "runs", run_name)
    best_pt = os.path.join(run_dir, "weights", "best.pt")
    
    if os.path.exists(best_pt):
        print(f"\n  📦 Mejor modelo guardado en:")
        print(f"     {best_pt}")
        print(f"\n  Para probar el modelo ejecuta:")
        print(f"     python test.py --model \"{best_pt}\"")
    else:
        # ultralytics a veces pone la carpeta diferente
        print(f"\n  📦 Revisa la carpeta runs/ para encontrar best.pt")
    
    print(f"\n  📊 Métricas y gráficos en:")
    print(f"     {run_dir}")
    print(f"{'='*60}\n")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entrena modelo YOLO")
    parser.add_argument("--model", type=str, default="yolov8n.pt", 
                        help="Modelo base (yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt)")
    parser.add_argument("--epochs", type=int, default=100, help="Número de épocas (default: 100)")
    parser.add_argument("--batch", type=int, default=16, help="Batch size (default: 16, reduce si poca VRAM)")
    parser.add_argument("--imgsz", type=int, default=640, help="Tamaño de imagen (default: 640)")
    parser.add_argument("--device", type=str, default='', help="Dispositivo: '' (auto), 'cpu', '0' (GPU)")
    parser.add_argument("--resume", action="store_true", help="Reanudar último entrenamiento")
    
    args = parser.parse_args()
    train(
        model_name=args.model,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        resume=args.resume,
    )
