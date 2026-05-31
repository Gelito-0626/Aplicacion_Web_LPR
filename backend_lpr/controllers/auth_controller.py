from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend_lpr.config import get_db
from backend_lpr.models.tablas import Usuario
from backend_lpr.schemas.validaciones import UsuarioCreate, UsuarioLogin

router = APIRouter(tags=["Autenticación y Personal"])

# 🔐 1. ENDPOINT DE LOGIN (Para iniciar sesión)
@router.post("/api/usuarios/login")
def login_usuario(datos: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter_by(correo_electronico=datos.correo_electronico).first()
    if not usuario or usuario.contrasena != datos.contrasena:
        return {"acceso": False, "motivo": "Usuario o contraseña incorrectos."}
    return {
        "acceso": True,
        "motivo": "Acceso autorizado",
        "nombre": usuario.nombre_apellido,
        "carnet_militar": usuario.carnet_militar
    }

# 👤 2. ENDPOINT DE REGISTRO (Para guardar personal nuevo)
@router.post("/api/usuarios/registro")
def registro_usuario(datos: UsuarioCreate, db: Session = Depends(get_db)):
    if db.query(Usuario).filter_by(correo_electronico=datos.correo_electronico).first():
        return {"registro": False, "motivo": "El correo ya está registrado."}
    if db.query(Usuario).filter_by(carnet_militar=datos.carnet_militar).first():
        return {"registro": False, "motivo": "El carnet militar ya está registrado."}

    # Guardar nuevo usuario
    usuario = Usuario(
        carnet_militar=datos.carnet_militar,
        nombre_apellido=datos.nombre_apellido,
        correo_electronico=datos.correo_electronico,
        rango=datos.rango,
        contrasena=datos.contrasena
    )
    db.add(usuario)
    db.commit()
    return {"registro": True, "motivo": "Usuario registrado correctamente."}