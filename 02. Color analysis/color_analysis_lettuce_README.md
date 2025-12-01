# Informe Técnico: Algoritmo de Segmentación Basado en Índices de Vegetación para Detección de Lechuga

**Fecha:** 01 de Diciembre, 2025  
**Contexto:** Visión por Computador / Procesamiento de Imágenes  
**Objeto de Estudio:** Segmentación de lechuga rallada (*Iceberg*) en bandejas de acero inoxidable.

---

## 1. Resumen Ejecutivo
El presente documento detalla la metodología algorítmica para la cuantificación de vegetales de hoja (lechuga). Debido a la baja saturación de la variedad "Iceberg" y la alta reflectividad de las bandejas metálicas (que a menudo generan reflejos amarillo-verdosos falsos), los métodos tradicionales de color fallan. La solución implementada adopta un enfoque de **Agricultura de Precisión**, utilizando el índice **ExG (Excess Green)** combinado con una normalización dinámica para distinguir biomasa real de ruido de fondo.

---
![Lettuce Results](results\lettuce_results.png)

## 2. Metodología

El desafío principal radica en que la suciedad en el metal puede tener un tono "verde limón" similar a la lechuga. Para resolver esto, el algoritmo abandona el espacio RGB tradicional en favor de un índice aritmético de contraste cromático.

### 2.1. Índice de Exceso de Verde (ExG - Excess Green Index)

Se utiliza una fórmula estándar en fotogrametría agrícola diseñada para separar vegetación del suelo (o en este caso, metal). Se opera sobre los canales flotantes de la imagen:

$$ExG(x,y) = 2 \times G(x,y) - R(x,y) - B(x,y)$$

**Fundamento Físico:**
* **Fondo Metálico (Gris/Blanco):** Al ser acromático, los tres canales tienen valores similares ($R \approx G \approx B$). La fórmula resulta en $2G - G - G \approx 0$.
* **Reflejos Cálidos (Amarillo):** El amarillo se forma con Rojo y Verde ($R \approx G$). La fórmula penaliza el componente rojo ($2G - G - B$), reduciendo significativamente su intensidad.
* **Lechuga (Verde):** El componente Verde es dominante ($G \gg R$ y $G \gg B$). La multiplicación ($2 \times G$) amplifica esta diferencia, generando un valor positivo alto.

### 2.2. Normalización Dinámica (Contrast Stretching)

Dado que la iluminación puede variar entre fotos, el valor absoluto del índice ExG no es constante. Se aplica una normalización **Min-Max** para re-escalar los valores calculados al rango de 8 bits $[0, 255]$:

$$N(x,y) = \frac{ExG(x,y) - \min(ExG)}{\max(ExG) - \min(ExG)} \times 255$$

Esto garantiza que el píxel "más verde" de la imagen siempre tenga el valor máximo (255), permitiendo un corte relativo consistente.

### 2.3. Umbralización Estricta de Alta Densidad

Para eliminar los "falsos positivos" (reflejos tenues o suciedad de la bandeja), se aplica una binarización con un umbral elevado. En la escala normalizada (visualizada típicamente como un mapa de calor *Jet*, donde el azul es bajo y el rojo es alto), buscamos aislar únicamente el núcleo denso de la vegetación.

**Parámetro de Corte:** $T = 150$

* **$Pixel < 150$:** Se descarta. Esto elimina el metal (azul oscuro en el mapa) y los reflejos verdosos débiles (zonas cian/verdes medias).
* **$Pixel \ge 150$:** Se conserva. Esto corresponde a las zonas naranjas y rojas del mapa de calor, asegurando que solo se cuenta la lechuga con alta confianza espectral.

### 2.4. Limpieza Morfológica (Noise Reduction)

A diferencia del tocino (donde se evitó la morfología), la lechuga rallada presenta una textura ruidosa y fragmentada. Para obtener una máscara limpia:

1.  **Erosión ($3\times3$):** Elimina el "ruido de sal" (píxeles blancos aislados) que logran superar el umbral pero no tienen volumen.
2.  **Dilatación ($3\times3$):** Restaura el tamaño original de los fragmentos de lechuga erosionados, suavizando los bordes sin inflar artificialmente el área.

---

## 3. Conclusión Técnica

La implementación del índice **ExG** demuestra ser superior a la segmentación por color HSV para vegetales pálidos en entornos metálicos. Al penalizar aritméticamente los canales Rojo y Azul, el algoritmo anula efectivamente el fondo gris. El ajuste del umbral a **150** actúa como un filtro de calidad ("Quality Gate"), permitiendo el paso únicamente a píxeles con una dominancia verde significativa, resolviendo el problema de distinción entre la bandeja sucia y el producto real.