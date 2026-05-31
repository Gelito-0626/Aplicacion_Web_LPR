from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de la base de datos SQLite (se creará en la raíz si no existe)
DATABASE_URL = "sqlite:///./database_lpr.db"

# Motor de conexión. El parámetro check_same_thread es esencial para FastAPI+SQLite
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Clase Base para tus modelos (tablas)
Base = declarative_base()

# Sesión para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependencia: Entrega una sesión lista para usar en endpoints (cerrándose sola)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()