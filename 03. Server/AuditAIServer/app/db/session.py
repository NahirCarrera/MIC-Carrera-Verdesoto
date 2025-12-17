from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# URL de conexión a tu Docker
# Formato: postgresql://usuario:password@localhost:puerto/nombre_db
SQLALCHEMY_DATABASE_URL = "postgresql://test_user:1234@localhost:5432/auditai_test_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Esta función se usará en los endpoints para abrir/cerrar conexión automáticamente
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()