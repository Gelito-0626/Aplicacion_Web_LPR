# main.py
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
import hashlib
import asyncio

from backend_lpr.config import engine, get_db, SessionLocal
from backend_lpr.models import tablas
from backend_lpr.models.tablas import Usuario
from backend_lpr.schemas.validaciones import DeteccionPlacaInput
from backend_lpr.controllers.acceso_controller import procesar_deteccion_placa, router as acceso_router
from backend_lpr.controllers.auth_controller import router as auth_router
from backend_lpr.controllers.vehiculo_controller import router as vehiculo_router
from backend_lpr.controllers.usuario_controller import router as usuario_router

print("🔧 Inicializando base de datos...")
tablas.Base.metadata.create_all(bind=engine)
print("✅ Base de datos lista")

db_admin = SessionLocal()
existe = db_admin.query(Usuario).filter_by(carnet_militar="00000000").first()
if not existe:
    admin = Usuario(
        carnet_militar="00000000",
        nombre_apellido="Administrador del Sistema",
        correo_electronico="comandante@seguridad.mil.ve",
        rango="Cnel",
        contrasena=hashlib.sha256("admin123".encode()).hexdigest()
    )
    db_admin.add(admin)
    db_admin.commit()
    print("✅ Usuario administrador creado: comandante@seguridad.mil.ve / admin123")
db_admin.close()

app = FastAPI(
    title="Aplicación Web LPR de Control Perimetral Autónomo",
    description="Sistema de Reconocimiento de Matrículas (LPR)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth_router)
app.include_router(vehiculo_router)
app.include_router(acceso_router)
app.include_router(usuario_router)

FRONTEND_DIR = "fronted_lpr"
if os.path.exists(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🔗 Cliente conectado (Total: {len(self.active_connections)})")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"🔌 Cliente desconectado (Total: {len(self.active_connections)})")
    
    async def broadcast(self, message: dict):
        desconectados = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                desconectados.append(connection)
        for conn in desconectados:
            self.disconnect(conn)

manager = ConnectionManager()

@app.websocket("/ws/monitoreo")
async def websocket_monitoreo(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"tipo": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

@app.post("/api/lpr/deteccion", tags=["Módulo de Inteligencia Artificial"])
async def recibir_deteccion_ia(datos: DeteccionPlacaInput, db: Session = Depends(get_db)):
    try:
        resultado = procesar_deteccion_placa(datos, db)
        await manager.broadcast({
            "tipo": "nueva_deteccion",
            "placa": resultado.get("placa"),
            "estado": resultado.get("estado"),
            "propietario": resultado.get("propietario"),
            "detalles": resultado.get("detalles"),
            "timestamp": datetime.now().isoformat()
        })
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/lpr/procesar-manual-broadcast", tags=["Módulo de Control"])
async def procesar_manual_broadcast(
    placa_manual: str = Form(...),
    db: Session = Depends(get_db)
):
    datos = DeteccionPlacaInput(placa=placa_manual, timestamp=datetime.now(), confianza=1.0, origen="manual")
    resultado = procesar_deteccion_placa(datos, db)
    
    await asyncio.sleep(0.1)
    await manager.broadcast({
        "tipo": "nueva_deteccion",
        "placa": resultado.get("placa"),
        "estado": resultado.get("estado"),
        "propietario": resultado.get("propietario"),
        "detalles": resultado.get("detalles"),
        "timestamp": datetime.now().isoformat()
    })
    
    return resultado

@app.get("/", tags=["Diagnóstico"])
def verificar_servidor():
    return {"status": "🟢 Servidor backend operativo", "sistema": "Control Perimetral LPR", "version": "2.0.0"}

@app.get("/health", tags=["Diagnóstico"])
def health_check():
    return {"status": "healthy", "database": "connected"}

@app.get("/status", tags=["Diagnóstico"])
def system_status():
    return {"servidor": "activo", "websocket": len(manager.active_connections)}

@app.get("/dashboard", tags=["Navegación"])
async def redirigir_dashboard():
    target = os.path.join(FRONTEND_DIR, "dashboard.html")
    if os.path.exists(target): return FileResponse(target)
    return {"error": "Dashboard no encontrado"}

@app.on_event("startup")
async def startup_event():
    print("🚀 SISTEMA LPR DESPLEGADO")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 SISTEMA DETENIDO")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")