# main.py
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os

# 📂 IMPORTACIONES LOGÍSTICAS (CORREGIDO: backend_lpr)
from backend_lpr.config import engine, get_db
from backend_lpr.models import tablas
from backend_lpr.schemas.validaciones import DeteccionPlacaInput
from backend_lpr.controllers.acceso_controller import procesar_deteccion_placa, router as acceso_router
from backend_lpr.controllers.auth_controller import router as auth_router
from backend_lpr.controllers.vehiculo_controller import router as vehiculo_router

# --- 1. Inicialización y creación automática de las tablas SQLite ---
print("🔧 Inicializando base de datos...")
tablas.Base.metadata.create_all(bind=engine)
print("✅ Base de datos lista")

# --- 2. Inicialización de la Aplicación FastAPI ---
app = FastAPI(
    title="Aplicación Web LPR de Control Perimetral Autónomo",
    description="""
    ## Sistema de Reconocimiento de Matrículas (LPR) - UNEFA
    
    ### Funcionalidades:
    * **Detección en tiempo real** de placas vehiculares mediante IA.
    * **Validación automática** de permisos de acceso institucional.
    * **Monitoreo por WebSocket** para alertas instantáneas en el Dashboard.
    * **Gestión de vehículos** (CRUD completo) autorizados y bloqueados.
    * **Control horario** estricto por días y horas permitidas.
    """,
    version="2.0.0",
    contact={
        "name": "UNEFA 2026",
        "description": "Desarrollo de Aplicación Web LPR Perimetral",
    }
)

# --- 3. Middleware de CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# --- 4. Incluir los routers del proyecto ---
app.include_router(auth_router)
app.include_router(vehiculo_router)
app.include_router(acceso_router)

print("📋 Routers cargados exitosamente:")
print("   - Auth Controller: /auth/*")
print("   - Vehículo Controller: /api/vehiculos/*")
print("   - Acceso Controller: /api/lpr/*")

# --- 5. Servir archivos estáticos del frontend ---
FRONTEND_DIR = "fronted_lpr"

if os.path.exists(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")
    print(f"🌐 Frontend disponible en: http://localhost:8000/frontend/dashboard.html")
else:
    print(f"⚠️ Alerta: No se detectó la carpeta '{FRONTEND_DIR}' en el directorio raíz.")

# --- 6. WebSocket MANAGER ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.connection_count = 0
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_count += 1
        print(f"🔗 Cliente conectado al Dashboard (Total: {len(self.active_connections)})")
        
        await websocket.send_json({
            "tipo": "conexion",
            "mensaje": "✅ Conectado al sistema de monitoreo LPR",
            "timestamp": datetime.now().isoformat(),
            "clientes_conectados": len(self.active_connections)
        })
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"🔌 Cliente desconectado del Dashboard (Total: {len(self.active_connections)})")
    
    async def broadcast(self, message: dict):
        desconectados = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"⚠️ Error enviando datos a la interfaz: {e}")
                desconectados.append(connection)
        
        for conn in desconectados:
            self.disconnect(conn)
    
    async def broadcast_alert(self, tipo: str, datos: dict):
        alerta = {
            "tipo": "alerta",
            "subtipo": tipo,
            "timestamp": datetime.now().isoformat(),
            "datos": datos
        }
        await self.broadcast(alerta)

manager = ConnectionManager()

# --- 7. ENDPOINT WebSocket para Monitoreo en Tiempo Real ---
@app.websocket("/ws/monitoreo")
async def websocket_monitoreo(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({
                    "tipo": "pong",
                    "timestamp": datetime.now().isoformat()
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("👋 Cliente cerró el Dashboard voluntariamente")
    except Exception as e:
        print(f"❌ Error en canal WebSocket: {e}")
        manager.disconnect(websocket)

# --- 8. ENDPOINT PARA LA IA ---
@app.post("/api/lpr/deteccion", tags=["Módulo de Inteligencia Artificial"])
async def recibir_deteccion_ia(
    datos: DeteccionPlacaInput,
    db: Session = Depends(get_db)
):
    try:
        print(f"📸 Lectura de cámara recibida: {datos.placa} (Confianza: {datos.confianza or 'N/A'})")
        
        resultado = procesar_deteccion_placa(datos, db)
        
        await manager.broadcast_alert(
            tipo="deteccion_placa",
            datos=resultado
        )
        
        estado = resultado.get("estado", "DESCONOCIDO")
        placa = resultado.get("placa", "???")
        propietario = resultado.get("propietario", "Desconocido")
        
        if estado == "PERMITIDO":
            print(f"✅ CONTROL PERIMETRAL - ACCESO PERMITIDO: {placa} - {propietario}")
        else:
            print(f"⛔ CONTROL PERIMETRAL - ACCESO DENEGADO: {placa} - {resultado.get('mensaje', 'Sin motivo')}")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Error procesando detección: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en el servidor LPR: {str(e)}"
        )

# --- 9. RUTAS DE DIAGNÓSTICO ---
@app.get("/", tags=["Diagnóstico"])
def verificar_servidor():
    return {
        "status": "🟢 Servidor backend operativo",
        "sistema": "Control Perimetral LPR - UNEFA 2026",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "clientes_conectados": len(manager.active_connections)
    }

@app.get("/health", tags=["Diagnóstico"])
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "clientes_websocket": len(manager.active_connections),
        "uptime": "running"
    }

@app.get("/status", tags=["Diagnóstico"])
def system_status():
    return {
        "servidor": {"estado": "activo", "version": "2.0.0"},
        "base_datos": {"estado": "conectada", "tipo": "SQLite", "archivo": "database.db"},
        "websocket": {"clientes_conectados": len(manager.active_connections)},
        "frontend": {"disponible": os.path.exists(FRONTEND_DIR)}
    }

# --- 10. REDIRECCIÓN AL DASHBOARD ---
@app.get("/dashboard", tags=["Navegación"])
async def redirigir_dashboard():
    target = os.path.join(FRONTEND_DIR, "dashboard.html")
    if os.path.exists(target):
        return FileResponse(target)
    return {"error": f"Archivo visual no encontrado en la ruta '{target}'"}

# --- 11. MANEJO DE EVENTOS ---
@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("🚀 SISTEMA DE MONITOREO LPR DESPLEGADO CON ÉXITO")
    print("=" * 60)
    print(f"📚 Documentación interactiva API: http://localhost:8000/docs")
    print(f"🖥️  Acceso directo al Dashboard:   http://localhost:8000/frontend/dashboard.html")
    print("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    print("\n" + "=" * 60)
    print("🛑 DETENIENDO SERVICIOS DE CONTROL PERIMETRAL")
    print(f"👥 Conexiones websocket cerradas de forma limpia: {len(manager.active_connections)}")
    print("=" * 60)

# --- 12. EJECUCIÓN DEL SERVIDOR ---
if __name__ == "__main__":
    import uvicorn
    print("🔥 Levantando entorno local...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )