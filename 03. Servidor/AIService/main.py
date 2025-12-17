from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from logic import FoodAnalyzer
import uvicorn

app = FastAPI(title="Servicio IA de Reconocimiento de Comida")
analyzer = FoodAnalyzer()

# Definimos el modelo de datos que esperamos recibir de .NET
class AnalysisRequest(BaseModel):
    image_path: str
    food_type: str  # onion, tomato, bacon, etc.

@app.post("/analyze")
def analyze_image(request: AnalysisRequest):
    """
    Recibe la ruta de la imagen y el tipo, devuelve el porcentaje.
    """
    # Normalizamos el tipo de comida a minúsculas
    f_type = request.food_type.lower()
    path = request.image_path

    try:
        if f_type == "pickles":
            result = analyzer.analyze_pickles(path)
        elif f_type == "pepper":
            result = analyzer.analyze_pepper(path)
        elif f_type == "onion":
            result = analyzer.analyze_onion(path)
        elif f_type == "lettuce":
            result = analyzer.analyze_lettuce(path)
        elif f_type == "bacon":
            result = analyzer.analyze_bacon(path)
        elif f_type == "tomato":
            result = analyzer.analyze_tomato(path)
        else:
            raise HTTPException(status_code=400, detail=f"Tipo de comida no soportado: {f_type}")
        
        # Respuesta exitosa
        return {
            "food_type": f_type,
            "percentage": result,
            "status": "success"
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# Bloque para correr el servidor localmente si ejecutas este script directo
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)