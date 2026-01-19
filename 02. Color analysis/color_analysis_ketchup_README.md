# Informe Técnico: Algoritmo de Segmentación Espectral para Detección de Condimentos Rojos (Ketchup)

**Fecha:** 19 de Enero, 2026
**Contexto:** Visión por Computador / Proyecto de Titulación Ingeniería de Software
**Objeto de Estudio:** Cuantificación de superficie de ketchup en bandejas industriales mediante análisis cromático.

---

## 1. Resumen Ejecutivo
La detección de ketchup se fundamenta en su firma espectral distintiva dentro del canal rojo. A diferencia de los aderezos claros, este producto presenta una baja reflectancia en las longitudes de onda cortas y medias (Azul y Verde), lo que permite utilizar la **aritmética de canales** para aislar la salsa del fondo. La solución implementada utiliza una sustracción espectral $R - G$ para anular las superficies acromáticas (bandejas grises/metálicas) y cuantificar el área ocupada con alta precisión.

---

## 2. Resultados Visuales

A continuación se presentan los resultados de la segmentación binaria y la generación de mapas de calor espectrales que validan la dominancia del canal rojo en el área de interés:

<div align="center">
  <img src="results/ketchup_results.png" width="700" alt="Resultados de Segmentación de Ketchu">
  <p><em>Figura 1: Comparativa entre la detección de contornos (Tray/Sauce) y el Mapa de Calor de Intensidad Cromática.</em></p>
</div>

---

## 3. Metodología

El algoritmo evita la umbralización por brillo global para prevenir errores causados por reflejos en la bandeja, optando por una discriminación basada en la pureza del color:

### 3.1. Pre-procesamiento y Atenuación de Ruido
Para eliminar artefactos de digitalización y suavizar la textura de la salsa, se aplica un **Filtro de Mediana** con un kernel de $7 \times 7$. Este filtro es particularmente efectivo para preservar los bordes de la bandeja mientras se eliminan ruidos de tipo "sal y pimienta" que podrían generar detecciones falsas.


### 3.2. Diferenciación Espectral de Canales (Channel Subtraction)
Se explota la propiedad física del ketchup: su alta concentración de licopenos genera una reflectancia dominante en el Rojo ($R$) y mínima en el Verde ($G$). Se calcula una imagen de diferencia $D(x,y)$:

$$D(x,y) = R(x,y) - G(x,y)$$

**Fundamento de Segmentación:**
* **Bandeja Industrial**: Al ser superficies grises, reflejan casi la misma cantidad de luz en todos los canales ($R \approx G$), por lo que $R - G \approx 0$.
* **Ketchup**: Debido a su color intenso, $R \gg G$, resultando en un valor positivo alto que resalta el producto sobre el fondo.


### 3.3. Generación de Mapas de Calor (Heatmaps)
Para visualizar la probabilidad de presencia de salsa, los valores de la diferencia $R - G$ se normalizan al rango $[0, 255]$ y se transforman mediante un mapa de color **JET**. Esto permite observar gradientes de concentración, donde el color rojo intenso en el mapa representa la mayor pureza cromática de la salsa.

### 3.4. Segmentación Binaria y Cuantificación
Se aplica un umbral estático de $T=18$ sobre la imagen de diferencia para generar la máscara final. Esta máscara se restringe estrictamente al área previamente identificada de la bandeja mediante una operación `bitwise_and`.

El porcentaje de llenado se calcula como:
$$P_{sauce} = \left( \frac{\text{Píxeles de Salsa}}{\text{Píxeles Totales de Bandeja}} \right) \times 100$$

---

## 4. Conclusión Técnica
La estrategia de **aritmética espectral** resulta altamente robusta para el ketchup debido a la naturaleza cromática del producto. Al anular matemáticamente los componentes grises del contenedor, el algoritmo minimiza el impacto de las sombras y variaciones de iluminación que suelen afectar a los métodos basados únicamente en escala de grises.