# app/db/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .session import Base

# 1. Catálogos (Tablas "pequeñas")
class VideoStatus(Base):
    __tablename__ = "video_status"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True) # Ej: PENDIENTE, PROCESADO

class InspectionStatus(Base):
    __tablename__ = "inspection_status"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))      # Ej: VACIO, LLENO
    severity = Column(Integer)     # 0=Bajo, 5=Crítico
    is_anomaly = Column(Boolean, default=False) # Para reportes rápidos

class FoodCategory(Base):
    __tablename__ = "food_category"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))        # Ej: Onion
    min_threshold = Column(Float)     # Umbral histórico (opcional si usas JSON)
    # Relación inversa (opcional)
    inspections = relationship("Inspection", back_populates="category")

# 2. Tablas Operativas
class SyncLog(Base):
    __tablename__ = "sync_log"
    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    found_videos = Column(Integer, default=0)
    processed_videos = Column(Integer, default=0)
    status = Column(String(50)) # RUNNING, SUCCESS, ERROR
    error_message = Column(Text, nullable=True)

    # Relación: Un log tiene muchos videos
    videos = relationship("Video", back_populates="sync_log")

class Video(Base):
    __tablename__ = "video"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), unique=True, index=True) # ID que viene de la cámara/sistema externo
    source_url = Column(String(255))
    date = Column(DateTime) # Fecha original del video
    
    # Llaves foráneas
    status_id = Column(Integer, ForeignKey("video_status.id"))
    log_id = Column(Integer, ForeignKey("sync_log.id")) # Relación con la importación
    
    # Relaciones
    status = relationship("VideoStatus")
    sync_log = relationship("SyncLog", back_populates="videos")
    inspections = relationship("Inspection", back_populates="video")

class Inspection(Base):
    __tablename__ = "inspection"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    video_minute = Column(Float, default=0.0)
    percentage = Column(Float)
    screenshot_url = Column(String(255))
    is_false_positive = Column(Boolean, default=False)
    model_version = Column(String(50))
    user_id_validator = Column(Integer, nullable=True)
    video_id = Column(Integer, ForeignKey("video.id"), nullable=True)
    
    category_id = Column(Integer, ForeignKey("food_category.id"))
    status_id = Column(Integer, ForeignKey("inspection_status.id"))
    
    # Relaciones
    video = relationship("Video")
    category = relationship("FoodCategory")
    status = relationship("InspectionStatus")