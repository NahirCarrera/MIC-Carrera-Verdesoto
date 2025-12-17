from fastapi import FastAPI
from app.api.endpoints import router as api_router

# 1. Crear la instancia de la aplicación
app = FastAPI(title="AuditAI")

# 2. Incluir las rutas que definimos en endpoints.py
# Esto conecta tu lógica de "analizar comida" con el servidor principal
app.include_router(api_router)

# 3. Ruta de prueba para verificar que el servidor vive
@app.get("/")
def read_root():
    return {"mensaje": "El servidor está corriendo correctamente"}

# No necesitas el bloque 'if __name__ == "__main__"' porque lo corres con uvicorn