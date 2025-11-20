# Generador de Datasets Automático (YOLO)


## Instrucciones de Uso

### PASO 1: Configuración de Coordenadas
**Archivo:** `coordinates.py`

Este script define el área de la pantalla y calcula el margen de movimiento permitido (*shake*) para la generación de datos.

1. **Ejecuta el script:** Aparecerá un marco **ROJO** siguiendo al cursor.
2. Mueve el mouse al centro del área a capturar y presiona **`ENTER`**.
   * Esto fija la zona de captura principal (Cuadro Rojo).
3. **Dibuja el "Cuadro Amarillo":**
   * Haz clic y arrastra desde el borde del objeto hacia adentro.
   * *Nota:* Este cuadro define el "área segura". La diferencia entre el cuadro rojo y el amarillo determina cuánto se moverá la cámara aleatoriamente.
4. **Controles:**
   * **`Z`**: Borrar y volver a intentar si te equivocas.
   * **`ENTER`**: Confirmar y guardar.

> 💾 **Resultado:** Se generará el archivo `coordinates_config.json`.

---

### PASO 2: Etiquetado (Labelling)
**Archivo:** `labelling.py`

Define dónde están los objetos (bandejas, ingredientes, items) dentro de la zona capturada.

1. Ejecuta el script (iniciará oculto).
2. Pon la aplicación en primer plano.
3. Presiona **`ALT` + `1`**.
   * El programa tomará una captura de fondo estática y abrirá el editor.
4. **Dibuja los objetos:**
   * Crea recuadros **VERDES** sobre cada objeto a detectar (clic y arrastrar).
5. **Controles:**
   * **`Z`**: Deshacer el último recuadro.
   * **`S`**: Guardar la configuración.

> 💾 **Resultado:** Se generará el archivo de configuración de anotaciones (ej. `labelling_config.json`).

---

### PASO 3: Captura de Datos (Screenshot)
**Archivo:** `screenshoot.py`

Este es el script principal. Utiliza las configuraciones anteriores para tomar múltiples capturas automáticamente, simulando movimiento y generando etiquetas `.txt` para YOLO.

1. Ejecuta el script (cargará los JSON automáticamente).
2. Presiona **`ALT` + `1`** para tomar una captura.
   * El script aplicará un ligero movimiento (*shake*) y guardará la imagen en `capturas_yolo`.
   * Guardará las etiquetas corregidas en `coordenadas_yolo`.

#### Modo Ajuste (Opcional)
Si la ventana del juego se movió de lugar:
1. Presiona **`ALT` + `2`** para entrar en Modo Ajuste.
2. Usa **`W`, `A`, `S`, `D`** para recolocar el cuadro de captura.
3. Presiona **`ALT` + `2`** nuevamente para guardar la nueva configuración.
4. Presiona **`ALT` + `ESC`** para cerrar el programa.

---

### PASO 4: Verificación
**Archivo:** `verification.py`

Auditoría del dataset para asegurar que las fotos y etiquetas coinciden.

1. Ejecuta el script. Se abrirá un visor con la última captura.
2. Verifica que los **Bounding Boxes** (recuadros verdes) coincidan perfectamente con los objetos.

[Image of YOLO object detection bounding box example]

**Controles del visor:**

| Tecla | Acción |
| :---: | :--- |
| **`🡢`** o **`D`** | Ver siguiente imagen |
| **`0`** o **`A`** | Ver imagen anterior |
| **`ESC`** o **`Q`** | Salir del visor |

---

> [!IMPORTANT]
> **Nota sobre Archivos:**
> Asegúrate de que el nombre del archivo generado en el **Paso 2** coincida con el que busca el script del **Paso 3**. Revisa la variable `TRAYS_CONFIG_FILE` en `screenshoot.py` si tienes problemas cargando las etiquetas.