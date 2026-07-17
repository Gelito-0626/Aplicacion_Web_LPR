from fastapi import Request, HTTPException
import logging

logger = logging.getLogger("aegis-security")

# Rutas públicas que no requieren autenticación
RUTAS_PUBLICAS = [
    "/", "/health", "/status", "/docs", "/openapi.json",
    "/api/usuarios/login", "/api/usuarios/registro",
    "/frontend", "/dashboard", "/ws/monitoreo"
]

async def verificar_autenticacion(request: Request):
    """Middleware de seguridad: verifica autenticación en rutas protegidas"""
    
    # Permitir rutas públicas sin token
    for ruta in RUTAS_PUBLICAS:
        if request.url.path.startswith(ruta):
            return
    
    # Verificar token en rutas protegidas
    token = request.headers.get("Authorization")
    if not token:
        logger.warning(f"⚠️ Acceso denegado sin token a {request.url.path}")
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de token inválido")
    
    return