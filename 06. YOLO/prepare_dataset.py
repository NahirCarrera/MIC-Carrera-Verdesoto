"""
prepare_dataset.py
==================
Toma las imágenes y etiquetas generadas por screenshoot.py (carpeta 01. Labelling data)
y las organiza en la estructura que YOLO necesita para entrenar:

    dataset/
    ├── train/
    │   ├── images/
    │   └── labels/
    └── val/
        ├── images/
        └── labels/

USO:
    python prepare_dataset.py

    --split 0.8       Proporción train/val (default: 80% train, 20% val)
    --shuffle          Mezclar imágenes antes de dividir (default: True)
    --seed 42          Semilla para reproducibilidad
"""

import os
import shutil
import random
import argparse
import glob

# ==========================================
#  CONFIGURACIÓN
# ==========================================

# Rutas de origen (relativas al proyecto)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

SOURCE_IMG_FOLDER = os.path.join(PROJECT_ROOT, "01. Labelling data", "capturas_yolo")
SOURCE_LABEL_FOLDER = os.path.join(PROJECT_ROOT, "01. Labelling data", "coordenadas_yolo")

# Ruta de destino
DATASET_DIR = os.path.join(SCRIPT_DIR, "dataset")

# Mapeo de clases (debe coincidir con labelling.py y screenshoot.py)
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


def count_dataset_stats(label_folder):
    """Cuenta cuántas imágenes hay por clase y cuántas son negativas."""
    class_counts = {cid: 0 for cid in CLASS_MAP}
    total_images = 0
    negative_images = 0
    
    for txt_file in glob.glob(os.path.join(label_folder, "*.txt")):
        total_images += 1
        with open(txt_file, 'r') as f:
            content = f.read().strip()
        
        if not content:
            negative_images += 1
            continue
        
        for line in content.split('\n'):
            parts = line.strip().split()
            if len(parts) >= 5:
                class_id = int(parts[0])
                if class_id in class_counts:
                    class_counts[class_id] += 1
    
    return total_images, negative_images, class_counts


def prepare_dataset(split_ratio=0.8, seed=42, shuffle=True):
    """
    Organiza el dataset en train/val con la estructura que YOLO espera.
    """
    print("=" * 60)
    print("  PREPARACIÓN DE DATASET YOLO")
    print("=" * 60)
    
    # 1. Verificar que existan las carpetas fuente
    if not os.path.exists(SOURCE_IMG_FOLDER):
        print(f"❌ No se encontró la carpeta de imágenes: {SOURCE_IMG_FOLDER}")
        return
    if not os.path.exists(SOURCE_LABEL_FOLDER):
        print(f"❌ No se encontró la carpeta de etiquetas: {SOURCE_LABEL_FOLDER}")
        return
    
    # 2. Listar todas las imágenes
    image_extensions = ['*.png', '*.jpg', '*.jpeg']
    all_images = []
    for ext in image_extensions:
        all_images.extend(glob.glob(os.path.join(SOURCE_IMG_FOLDER, ext)))
    
    if not all_images:
        print(f"❌ No hay imágenes en {SOURCE_IMG_FOLDER}")
        return
    
    # 3. Verificar que cada imagen tenga su .txt correspondiente
    valid_pairs = []
    missing_labels = 0
    
    for img_path in all_images:
        filename = os.path.splitext(os.path.basename(img_path))[0]
        label_path = os.path.join(SOURCE_LABEL_FOLDER, filename + ".txt")
        
        if os.path.exists(label_path):
            valid_pairs.append((img_path, label_path))
        else:
            missing_labels += 1
    
    print(f"\n📊 ESTADÍSTICAS DE ORIGEN:")
    print(f"   Imágenes totales:    {len(all_images)}")
    print(f"   Pares válidos:       {len(valid_pairs)}")
    if missing_labels > 0:
        print(f"   ⚠️  Sin etiqueta:     {missing_labels} (se omiten)")
    
    # 4. Mostrar distribución de clases
    total, negatives, class_counts = count_dataset_stats(SOURCE_LABEL_FOLDER)
    print(f"\n📋 DISTRIBUCIÓN DE CLASES:")
    print(f"   {'Clase':<4} {'Nombre':<12} {'Instancias':>10}")
    print(f"   {'─'*4} {'─'*12} {'─'*10}")
    for cid, name in CLASS_MAP.items():
        count = class_counts.get(cid, 0)
        bar = '█' * min(count // 5, 30) if count > 0 else ''
        print(f"   {cid:<4} {name:<12} {count:>10}  {bar}")
    print(f"\n   Negative samples:    {negatives}")
    pct_neg = (negatives / total * 100) if total > 0 else 0
    print(f"   Proporción negativas: {pct_neg:.1f}%")
    
    # 5. Mezclar y dividir
    if shuffle:
        random.seed(seed)
        random.shuffle(valid_pairs)
    
    split_idx = int(len(valid_pairs) * split_ratio)
    train_pairs = valid_pairs[:split_idx]
    val_pairs = valid_pairs[split_idx:]
    
    print(f"\n✂️  SPLIT ({split_ratio*100:.0f}/{(1-split_ratio)*100:.0f}):")
    print(f"   Train: {len(train_pairs)} imágenes")
    print(f"   Val:   {len(val_pairs)} imágenes")
    
    # 6. Crear estructura de carpetas
    dirs = {
        "train_img": os.path.join(DATASET_DIR, "train", "images"),
        "train_lbl": os.path.join(DATASET_DIR, "train", "labels"),
        "val_img":   os.path.join(DATASET_DIR, "val", "images"),
        "val_lbl":   os.path.join(DATASET_DIR, "val", "labels"),
    }
    
    # Limpiar dataset anterior si existe
    if os.path.exists(DATASET_DIR):
        print(f"\n🗑️  Limpiando dataset anterior...")
        shutil.rmtree(DATASET_DIR)
    
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    
    # 7. Copiar archivos
    print(f"\n📁 Copiando archivos...")
    
    for img_path, label_path in train_pairs:
        fname = os.path.basename(img_path)
        lname = os.path.basename(label_path)
        shutil.copy2(img_path, os.path.join(dirs["train_img"], fname))
        shutil.copy2(label_path, os.path.join(dirs["train_lbl"], lname))
    
    for img_path, label_path in val_pairs:
        fname = os.path.basename(img_path)
        lname = os.path.basename(label_path)
        shutil.copy2(img_path, os.path.join(dirs["val_img"], fname))
        shutil.copy2(label_path, os.path.join(dirs["val_lbl"], lname))
    
    print(f"   ✅ Train: {len(train_pairs)} copiados a dataset/train/")
    print(f"   ✅ Val:   {len(val_pairs)} copiados a dataset/val/")
    
    # 8. Verificar
    print(f"\n📂 ESTRUCTURA FINAL:")
    for key, path in dirs.items():
        count = len(os.listdir(path))
        print(f"   {path.replace(SCRIPT_DIR, '.')}  →  {count} archivos")
    
    print(f"\n{'='*60}")
    print(f"  ✅ Dataset listo en: {DATASET_DIR}")
    print(f"  → Ahora ejecuta: python train.py")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepara dataset YOLO desde capturas")
    parser.add_argument("--split", type=float, default=0.8, help="Proporción train (default: 0.8)")
    parser.add_argument("--seed", type=int, default=42, help="Semilla random (default: 42)")
    parser.add_argument("--no-shuffle", action="store_true", help="No mezclar imágenes")
    
    args = parser.parse_args()
    prepare_dataset(split_ratio=args.split, seed=args.seed, shuffle=not args.no_shuffle)
