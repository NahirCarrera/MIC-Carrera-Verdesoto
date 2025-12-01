# Informe Técnico: Algoritmo de Segmentación Espectral para Detección de Proteína Cárnica (Tocino)

**Fecha:** 26 de Noviembre, 2025  
**Contexto:** Visión por Computador / Procesamiento de Imágenes  
**Objeto de Estudio:** Segmentación de tocino frito en bandejas de acero inoxidable.

---

## 1. Resumen Ejecutivo
El presente documento detalla la metodología algorítmica para la cuantificación de tocino. A diferencia de los vegetales claros, la proteína cárnica presenta una firma espectral distintiva en el canal rojo. La solución implementada explota la **aritmética de canales** para anular el fondo metálico (acromático) y utiliza una estrategia de **fusión de sensores virtuales** (RGB + HSV) para recuperar zonas de baja luminancia (zonas "quemadas" o muy oscuras).

---
### Resultados Visuales

A continuación se presentan los resultados de la segmentación mediante aritmética de canales (R-G) y fusión con máscara oscura HSV:

<div align="center">
  <img src="results/bacon_results.png" width="700" alt="Gráfica de Resultados de Tocino">
  <p><em>Figura 1: Comparativa entre imagen original y mapa de calor espectral (Dominancia Roja).</em></p>
</div>

## 2. Metodología

El algoritmo evita el uso de umbralización simple por brillo, dado que la grasa del tocino y el metal pueden compartir niveles de intensidad. Se opta por un enfoque basado en crominancia:

### 2.1. Diferenciación Espectral de Canales (Channel Subtraction)

Se aprovecha la propiedad física de la superficie metálica: al ser gris/plateada, refleja la luz de manera uniforme en todo el espectro visible ($R \approx G \approx B$). Por el contrario, el tocino presenta una dominancia en la longitud de onda larga (Rojo).

Se calcula una imagen de diferencia $D(x,y)$ mediante la sustracción aritmética del canal Verde ($G$) sobre el canal Rojo ($R$):

$$D(x,y) = R(x,y) - G(x,y)$$

**Fundamento Físico:**
* **Fondo Metálico:** Como $R \approx G$, entonces $R - G \to 0$ (El fondo se vuelve negro).
* **Tocino:** Como $R \gg G$, entonces $R - G \to \text{Valor Alto}$ (El objeto se resalta).

### 2.2. Expansión del Rango Dinámico (Histogram Normalization)

La señal resultante de la diferencia $D(x,y)$ puede tener un contraste bajo. Para garantizar una binarización robusta, se aplica una **Normalización Min-Max** para estirar el histograma y ocupar todo el rango de 8 bits $[0, 255]$:

$$N(x,y) = \frac{D(x,y) - \min(D)}{\max(D) - \min(D)} \times 255$$

Posteriormente, se aplica una umbralización binaria con corte en $T=135$ para aislar las zonas de alta crominancia roja.

### 2.3. Fusión Multi-Espectral (RGB + HSV Fusion)

La sustracción de canales (Paso 2.1) es excelente para la carne roja, pero falla en zonas carbonizadas o muy oscuras (donde $R$ y $G$ son ambos muy bajos). Para mitigar esto, se introduce una vía paralela de detección en el espacio de color **HSV (Matiz, Saturación, Valor)**.

Se genera una máscara secundaria $M_{dark}$ dirigida específicamente a tonos marrones/oscuros:
* **Matiz ($H$):** Rango $[0, 180]$ (Todo el espectro de rojos/naranjas).
* **Saturación ($S$):** Rango $[20, 255]$ (Para evitar grises).
* **Valor ($V$):** Rango $[0, 60]$ (Exclusivamente zonas muy oscuras).

Finalmente, se realiza una operación lógica **OR (Unión)** entre la máscara espectral y la máscara HSV:

$$M_{final} = M_{spectral} \cup M_{dark}$$

### 2.4. Extracción de Fronteras de Alta Fidelidad

Dado que el producto (tocino) presenta bordes irregulares y texturas finas que son críticas para una medición precisa del área, se ha suprimido deliberadamente cualquier operación de **Filtrado Morfológico** (Erosión/Dilatación).

Se utiliza la extracción de contornos con codificación de cadena completa:
* **Algoritmo:** `cv2.findContours` con `cv2.CHAIN_APPROX_NONE`.
* **Justificación:** Se preserva la rugosidad natural del borde del objeto. La aproximación poligonal o el suavizado morfológico introducirían un sesgo negativo en el cálculo del área al "recortar" las irregularidades microscópicas propias de la textura del tocino.

---

## 3. Conclusión Técnica

La estrategia implementada combina la **selectividad cromática** (para eliminar el fondo metálico que actúa como espejo neutro) con la **robustez en baja luminancia** del espacio HSV. La decisión de evitar el suavizado morfológico garantiza que la métrica de ocupación refleje la geometría real y "cruda" del producto, maximizando la precisión en la estimación de cobertura.