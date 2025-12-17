import cv2
import numpy as np
import json
import os
from sqlalchemy.orm import Session
from app.db.models import FoodCategory

class FoodColorAnalyzer:
    def __init__(self, config_filename="config_food.json"):
        # Busca el JSON en la misma carpeta que este script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, config_filename)
        
        print(f"🔍 Buscando configuración técnica en: {config_path}") 
        
        self.config = self._load_config(config_path)
        
        # Mapeo de métodos
        self._analysis_methods = {
            "pickles": self._analyze_pickles,
            "tomato": self._analyze_tomato,
            "pepper": self._analyze_pepper,
            "onion": self._analyze_onion,
            "lettuce": self._analyze_lettuce,
            "bacon": self._analyze_bacon,
        }

    def _load_config(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"No se encontró el archivo de configuración: {path}")
        with open(path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                raise ValueError(f"Error al decodificar el JSON en: {path}")

    def _get_config_for(self, food_type):
        """Obtiene la configuración TÉCNICA (kernels, colores) del JSON."""
        cfg = self.config.get(food_type)
        if not cfg:
            raise ValueError(f"No existe configuración técnica para: {food_type}")
        return cfg

    def _calculate_final_percentage(self, mask, img_shape):
        """Helper matemático."""
        food_pixels = cv2.countNonZero(mask)
        total_pixels = img_shape[0] * img_shape[1]
        if total_pixels == 0: return 0.0
        return round((food_pixels / total_pixels) * 100, 2)

    def _get_structuring_element(self, shape_type, size_list):
        return cv2.getStructuringElement(shape_type, tuple(size_list))
    
    def analyze_image_matrix(self, img_matrix: np.ndarray, food_type: str, db: Session) -> dict:
        """
        1. Calcula el porcentaje usando parámetros técnicos (JSON).
        2. Obtiene el umbral de decisión desde la Base de Datos (SQLite).
        3. Decide si es INCIDENTE o NORMAL.
        """
        if img_matrix is None or img_matrix.size == 0:
            raise ValueError("La imagen de entrada está vacía o es nula.")

        food_type_key = food_type.lower().strip()
        analysis_method = self._analysis_methods.get(food_type_key)

        if not analysis_method:
            raise ValueError(f"Tipo de comida no soportado: {food_type_key}")

        # --- PASO A: Consultar Base de Datos ---
        food_category_db = db.query(FoodCategory).filter(FoodCategory.name == food_type_key).first()
        
        if not food_category_db:
            # Fallback de seguridad por si olvidaste correr el seeder para esta comida
            raise ValueError(f"La comida '{food_type_key}' no existe en la tabla 'food_category' de la BD.")

        db_min_threshold = food_category_db.min_threshold

        # --- PASO B: Análisis de Imagen (Matemática) ---
        current_percentage = analysis_method(img_matrix)

        # --- PASO C: Decisión de Negocio ---
        is_incident = current_percentage < db_min_threshold
        status_msg = "INCIDENTE" if is_incident else "NORMAL"

        return {
            "percentage": current_percentage,
            "min_threshold": db_min_threshold,
            "is_incident": is_incident,
            "status": status_msg
        }

    def _analyze_pickles(self, img):
        cfg = self._get_config_for("pickles")
        img_blur = cv2.GaussianBlur(img, (3, 3), 0)
        img_float = img_blur.astype(np.float32)
        b, g, r = cv2.split(img_float)
        exg = 2 * g - r - b
        exg_norm = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        _, mask_exg = cv2.threshold(exg_norm, cfg['exg_threshold'], 255, cv2.THRESH_BINARY)
        hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV)
        s_channel = hsv[:,:,1]
        _, mask_sat = cv2.threshold(s_channel, cfg['saturation_threshold'], 255, cv2.THRESH_BINARY)
        mask_combined = cv2.bitwise_and(mask_exg, mask_sat)
        kernel_small = self._get_structuring_element(cv2.MORPH_ELLIPSE, cfg['morph_kernel_size'])
        mask_closed = cv2.morphologyEx(mask_combined, cv2.MORPH_CLOSE, kernel_small, iterations=1)
        mask_final = cv2.erode(mask_closed, kernel_small, iterations=1)
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask_final)
        for cnt in contours:
            if cv2.contourArea(cnt) > cfg['min_contour_area']:
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)
        return self._calculate_final_percentage(mask_filtered, img.shape)

    def _analyze_tomato(self, img):
        cfg = self._get_config_for("tomato")
        img_blur = cv2.GaussianBlur(img, (3, 3), 0)
        b, g, r = cv2.split(img_blur)
        diff_rg = cv2.subtract(r, g)
        norm_diff = cv2.normalize(diff_rg, None, 0, 255, cv2.NORM_MINMAX)
        _, mask_spectral = cv2.threshold(norm_diff, cfg['spectral_threshold'], 255, cv2.THRESH_BINARY)
        hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV)
        s_channel = hsv[:,:,1]
        _, mask_sat = cv2.threshold(s_channel, cfg['saturation_threshold'], 255, cv2.THRESH_BINARY)
        mask_combined = cv2.bitwise_and(mask_spectral, mask_sat)
        kernel = self._get_structuring_element(cv2.MORPH_ELLIPSE, cfg['morph_kernel_size'])
        mask_final = cv2.morphologyEx(mask_combined, cv2.MORPH_OPEN, kernel, iterations=1)
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask_final)
        for cnt in contours:
            if cv2.contourArea(cnt) > cfg['min_contour_area']:
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)
        return self._calculate_final_percentage(mask_filtered, img.shape)

    def _analyze_pepper(self, img):
        cfg = self._get_config_for("pepper")
        img_blur = cv2.GaussianBlur(img, (5, 5), 0)
        lab = cv2.cvtColor(img_blur, cv2.COLOR_BGR2LAB)
        _, _, b_channel = cv2.split(lab)
        _, mask = cv2.threshold(b_channel, cfg['b_channel_threshold'], 255, cv2.THRESH_BINARY)
        kernel_close = np.ones(tuple(cfg['close_kernel_size']), np.uint8)
        mask_closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        kernel_erode = np.ones(tuple(cfg['erode_kernel_size']), np.uint8)
        mask_final = cv2.erode(mask_closed, kernel_erode, iterations=1)
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask_final)
        for cnt in contours:
            if cv2.contourArea(cnt) > cfg['min_contour_area']:
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)
        return self._calculate_final_percentage(mask_filtered, img.shape)

    def _analyze_onion(self, img):
        cfg = self._get_config_for("onion")
        img_dimmed = cv2.convertScaleAbs(img, alpha=0.8, beta=0)
        gray = cv2.cvtColor(img_dimmed, cv2.COLOR_BGR2GRAY)
        mask_final = cv2.inRange(gray, cfg['gray_lower'], cfg['gray_upper'])
        mask_filtered = mask_final
        return self._calculate_final_percentage(mask_filtered, img.shape)

    def _analyze_lettuce(self, img):
        cfg = self._get_config_for("lettuce")
        img_float = img.astype(np.float32)
        b, g, r = cv2.split(img_float)
        exg = 2 * g - r - b
        exg_norm = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        _, mask = cv2.threshold(exg_norm, cfg['exg_threshold'], 255, cv2.THRESH_BINARY)
        kernel_clean = np.ones((3, 3), np.uint8)
        mask_clean = cv2.erode(mask, kernel_clean, iterations=1)
        mask_final = cv2.dilate(mask_clean, kernel_clean, iterations=1)
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask_final)
        for cnt in contours:
            if cv2.contourArea(cnt) > cfg['min_contour_area']:
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)
        return self._calculate_final_percentage(mask_filtered, img.shape)

    def _analyze_bacon(self, img):
        cfg = self._get_config_for("bacon")
        b, g, r = cv2.split(img)
        diff_rg = cv2.subtract(r, g)
        norm_diff = cv2.normalize(diff_rg, None, 0, 255, cv2.NORM_MINMAX)
        _, mask = cv2.threshold(norm_diff, cfg['diff_threshold'], 255, cv2.THRESH_BINARY)
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_hsv = np.array(cfg['dark_hsv_lower'])
        upper_hsv = np.array(cfg['dark_hsv_upper'])
        mask_dark = cv2.inRange(hsv, lower_hsv, upper_hsv)
        mask = cv2.bitwise_or(mask, mask_dark)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask)
        
        for cnt in contours:
            if cv2.contourArea(cnt) > cfg['min_contour_area']:
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)
        return self._calculate_final_percentage(mask_filtered, img.shape)