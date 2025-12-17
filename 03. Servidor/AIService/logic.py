import cv2
import numpy as np
import os

class FoodAnalyzer:
    
    @staticmethod
    def _load_image(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"La imagen no existe en: {path}")
        img = cv2.imread(path)
        if img is None:
            raise ValueError("No se pudo leer la imagen (formato incorrecto o corrupto).")
        return img

    @staticmethod
    def _calculate_percent(mask, img_shape):
        food_pixels = cv2.countNonZero(mask)
        total_pixels = img_shape[0] * img_shape[1]
        return round((food_pixels / total_pixels) * 100, 2)

    def analyze_pickles(self, path):
        img = self._load_image(path)
        img_blur = cv2.GaussianBlur(img, (3, 3), 0)
        
        # ExG
        img_float = img_blur.astype(np.float32)
        b, g, r = cv2.split(img_float)
        exg = 2 * g - r - b
        exg_norm = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        _, mask_exg = cv2.threshold(exg_norm, 110, 255, cv2.THRESH_BINARY)

        # Saturación
        hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV)
        s_channel = hsv[:,:,1]
        _, mask_sat = cv2.threshold(s_channel, 40, 255, cv2.THRESH_BINARY)

        mask_combined = cv2.bitwise_and(mask_exg, mask_sat)
        
        # Morfología
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        mask_closed = cv2.morphologyEx(mask_combined, cv2.MORPH_CLOSE, kernel_small, iterations=1)
        mask_final = cv2.erode(mask_closed, kernel_small, iterations=1)

        # Filtro de área simple
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask_final)
        for cnt in contours:
            if cv2.contourArea(cnt) > 30:
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)

        return self._calculate_percent(mask_filtered, img.shape)

    def analyze_pepper(self, path):
        img = self._load_image(path)
        img_blur = cv2.GaussianBlur(img, (5, 5), 0)
        
        # LAB -> Canal B
        lab = cv2.cvtColor(img_blur, cv2.COLOR_BGR2LAB)
        _, _, b_channel = cv2.split(lab)
        _, mask = cv2.threshold(b_channel, 147, 255, cv2.THRESH_BINARY)

        # Morfología
        kernel_close = np.ones((5,5), np.uint8) 
        mask_closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        kernel_erode = np.ones((3,3), np.uint8)
        mask_final = cv2.erode(mask_closed, kernel_erode, iterations=1)

        # Filtro área
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask_final)
        for cnt in contours:
            if cv2.contourArea(cnt) > 50: 
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)

        return self._calculate_percent(mask_filtered, img.shape)

    def analyze_onion(self, path):
        img = self._load_image(path)
        img_dimmed = cv2.convertScaleAbs(img, alpha=0.8, beta=0)
        gray = cv2.cvtColor(img_dimmed, cv2.COLOR_BGR2GRAY)
        
        # Banda estrecha
        mask_final = cv2.inRange(gray, 145, 170)
        
        return self._calculate_percent(mask_final, img.shape)

    def analyze_lettuce(self, path):
        img = self._load_image(path)
        img_float = img.astype(np.float32)
        b, g, r = cv2.split(img_float)
        
        # ExG
        exg = 2 * g - r - b
        exg_norm = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        _, mask = cv2.threshold(exg_norm, 150, 255, cv2.THRESH_BINARY)

        kernel_clean = np.ones((3,3), np.uint8)
        mask_clean = cv2.erode(mask, kernel_clean, iterations=1)
        mask_final = cv2.dilate(mask_clean, kernel_clean, iterations=1)

        # Filtro área
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask_final)
        for cnt in contours:
            if cv2.contourArea(cnt) > 30: 
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)

        return self._calculate_percent(mask_filtered, img.shape)

    def analyze_bacon(self, path):
        img = self._load_image(path)
        b, g, r = cv2.split(img)
        diff_rg = cv2.subtract(r, g)
        norm_diff = cv2.normalize(diff_rg, None, 0, 255, cv2.NORM_MINMAX)
        _, mask = cv2.threshold(norm_diff, 135, 255, cv2.THRESH_BINARY)

        # Recuperar zonas oscuras (quemado)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask_dark = cv2.inRange(hsv, np.array([0, 20, 0]), np.array([180, 255, 60]))
        mask = cv2.bitwise_or(mask, mask_dark)

        # Filtro de área simple
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_final = np.zeros_like(mask)
        for cnt in contours:
            if cv2.contourArea(cnt) > 400: 
                cv2.drawContours(mask_final, [cnt], -1, 255, -1)

        return self._calculate_percent(mask_final, img.shape)

    def analyze_tomato(self, path):
        img = self._load_image(path)
        img_blur = cv2.GaussianBlur(img, (3, 3), 0)
        b, g, r = cv2.split(img_blur)
        diff_rg = cv2.subtract(r, g)
        norm_diff = cv2.normalize(diff_rg, None, 0, 255, cv2.NORM_MINMAX)
        
        # Umbral estricto
        _, mask_spectral = cv2.threshold(norm_diff, 120, 255, cv2.THRESH_BINARY)
        
        # Filtro saturación
        hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV)
        s_channel = hsv[:,:,1]
        _, mask_sat = cv2.threshold(s_channel, 60, 255, cv2.THRESH_BINARY)

        mask_combined = cv2.bitwise_and(mask_spectral, mask_sat)
        
        # Morfología Open
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        mask_final = cv2.morphologyEx(mask_combined, cv2.MORPH_OPEN, kernel, iterations=1)

        # Filtro área
        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        mask_filtered = np.zeros_like(mask_final)
        for cnt in contours:
            if cv2.contourArea(cnt) > 30: 
                cv2.drawContours(mask_filtered, [cnt], -1, 255, -1)

        return self._calculate_percent(mask_filtered, img.shape)