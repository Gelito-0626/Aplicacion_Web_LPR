from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend_lpr.config import get_db
from backend_lpr.models.tablas import Usuario
from backend_lpr.schemas.validaciones import UsuarioCreate
import hashlib

router = APIRouter(prefix="/api/usuarios", tags=["Gestión de Usuarios"])

def hash_clave(clave: str) -> str:
    return hashlib.sha256(clave.encode()).hexdigest()

@router.get("/listar")
def listar_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(Usuario).all()
    return {
        "usuarios": [
            {
                "carnet_militar": u.carnet_militar,
                "nombre_apellido": u.nombre_apellido,
                "correo_electronico": u.correo_electronico,
                "rango": u.rango
            }
            for u in usuarios
        ]
    }

@router.get("/buscar/{carnet}")
def buscar_usuario(carnet: str, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter_by(carnet_militar=carnet).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "carnet_militar": u.carnet_militar,
        "nombre_apellido": u.nombre_apellido,
        "correo_electronico": u.correo_electronico,
        "rango": u.rango
    }

@router.put("/actualizar/{carnet}")
def actualizar_usuario(carnet: str, datos: UsuarioCreate, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter_by(carnet_militar=carnet).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    u.nombre_apellido = datos.nombre_apellido
    u.correo_electronico = datos.correo_electronico
    u.rango = datos.rango
    if datos.contrasena and datos.contrasena != "unefa123":
        u.contrasena = hash_clave(datos.contrasena)
    
    db.commit()
    return {"actualizado": True, "motivo": "Usuario actualizado exitosamente"}

@router.delete("/eliminar/{carnet}")
def eliminar_usuario(carnet: str, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter_by(carnet_militar=carnet).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(u)
    db.commit()
    return {"eliminado": True, "motivo": f"Usuario {carnet} eliminado exitosamente"}