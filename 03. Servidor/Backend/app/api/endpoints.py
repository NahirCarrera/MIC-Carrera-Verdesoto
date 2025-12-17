from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
import numpy as np
import cv2
from datetime import datetime
import os

from app.services.food_analysis import FoodColorAnalyzer
from app.db.session import get_db
from app.db.models import Inspection, InspectionStatus, FoodCategory

router = APIRouter()

# Load technical configuration (JSON) on startup
try:
    analyzer = FoodColorAnalyzer("config_food.json") 
    print("AI Service loaded successfully.")
except Exception as e:
    print(f"Error loading AI Service: {e}")
    analyzer = None

@router.post("/analyze-food")
async def analyze_food_endpoint(
    type: str = Form(..., description="Food type"),
    user_id: int = Form(..., description="Laravel User ID"),
    
    # --- NUEVO PARAMETRO RECIBIDO ---
    image_url: str = Form(..., description="URL real de la imagen en Laravel"),
    
    file: UploadFile = File(..., description="Image"),
    db: Session = Depends(get_db)
):
    if analyzer is None:
        raise HTTPException(status_code=500, detail="Servicio IA no disponible")

    # 1. Leer imagen (En Memoria RAM)
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_matrix = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_matrix is None:
        raise HTTPException(status_code=400, detail="Imagen inválida o corrupta")

    try:
        # 2. ANALYZE
        result = analyzer.analyze_image_matrix(img_matrix, type, db)
        
        # 3. SAVE TO DB
        status_name = "INCIDENT" if result["is_incident"] else "NORMAL"
        
        # Buscamos IDs foráneos
        db_status = db.query(InspectionStatus).filter_by(name=status_name).first()
        db_category = db.query(FoodCategory).filter_by(name=type.lower()).first()

        new_inspection = Inspection(
            video_id=None, 
            category_id=db_category.id if db_category else None,
            status_id=db_status.id if db_status else None,
            user_id_validator=user_id,
            video_minute=0.0,
            percentage=float(result["percentage"]),
            is_false_positive=False,
            model_version="Image-Prototype-v1",
            
            # --- CAMBIO IMPORTANTE: Usamos la URL que nos mandó Laravel ---
            screenshot_url=image_url 
        )
        db.add(new_inspection)
        db.commit()

        # 4. Respond
        return {
            "status": "success",
            "food_type": type,
            "filename": file.filename,
            "percentage": result["percentage"],
            "min_threshold": result["min_threshold"], 
            "is_incident": result["is_incident"],
            "incident_status": result["status"]
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Detailed error: {e}") 
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")