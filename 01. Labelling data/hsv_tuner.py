import cv2
import numpy as np

def nothing(x):
    pass

# CAMBIA ESTO por la ruta de la imagen que quieres corregir (ej. la "Low" o la "Medium")
image_path = "color_standard/bacon/05. low.png" 

# Cargar imagen
image = cv2.imread(image_path)
if image is None:
    print(f"No se encontró la imagen: {image_path}")
    exit()

# Redimensionar para que quepa en pantalla si es muy grande
image = cv2.resize(image, (600, 600)) 

# Crear ventana
cv2.namedWindow('Afinador HSV')

# Crear Trackbars (Deslizadores)
# Rango inicial sugerido para carne:
# H: 0-20 (Rojos/Naranjas)
# S: 60-255 (Saturación media-alta para evitar el gris de la bandeja)
# V: 30-255 (Brillo bajo para detectar lo quemado)

cv2.createTrackbar('H Min', 'Afinador HSV', 0, 179, nothing)
cv2.createTrackbar('S Min', 'Afinador HSV', 60, 255, nothing) # CLAVE PARA LA BANDEJA
cv2.createTrackbar('V Min', 'Afinador HSV', 30, 255, nothing) # CLAVE PARA LO QUEMADO

cv2.createTrackbar('H Max', 'Afinador HSV', 20, 179, nothing)
cv2.createTrackbar('S Max', 'Afinador HSV', 255, 255, nothing)
cv2.createTrackbar('V Max', 'Afinador HSV', 255, 255, nothing)

while True:
    # 1. Obtener valores actuales de los sliders
    h_min = cv2.getTrackbarPos('H Min', 'Afinador HSV')
    s_min = cv2.getTrackbarPos('S Min', 'Afinador HSV')
    v_min = cv2.getTrackbarPos('V Min', 'Afinador HSV')
    h_max = cv2.getTrackbarPos('H Max', 'Afinador HSV')
    s_max = cv2.getTrackbarPos('S Max', 'Afinador HSV')
    v_max = cv2.getTrackbarPos('V Max', 'Afinador HSV')

    # 2. Convertir a HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 3. Crear límites
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])

    # 4. Crear máscara
    mask = cv2.inRange(hsv, lower, upper)

    # 5. Visualizar
    # Resultado final: La imagen original donde la máscara es blanca
    result = cv2.bitwise_and(image, image, mask=mask)

    # Apilar imágenes para verlas juntas (Original | Máscara | Resultado)
    mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    stacked = np.hstack([mask_bgr, result])

    cv2.imshow('Afinador HSV', stacked)

    # Salir con ESC
    k = cv2.waitKey(1) & 0xFF
    if k == 27:
        break

    # Imprimir valores al presionar 'P' para copiarlos luego
    if k == ord('p'):
        print(f"Tus valores -> Lower: [{h_min}, {s_min}, {v_min}], Upper: [{h_max}, {s_max}, {v_max}]")

cv2.destroyAllWindows()