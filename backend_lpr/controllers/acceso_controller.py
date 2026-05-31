from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from backend_lpr.config import get_db            # ✅ CORREGIDO
from backend_lpr.models.tablas import Vehiculo    # ✅ CORREGIDO

router = APIRouter()

def verificar_horario_acceso(vehiculo, hora_actual: str, dia_actual: int) -> bool:
    """
    Verifica si el vehículo tiene permiso en el día y hora actual
    """
    # Si no tiene restricciones horarias, se permite el acceso
    if not vehiculo.hora_inicio or not vehiculo.hora_fin:
        return True
    
    # Verificar día permitido
    if vehiculo.dias_permitidos:
        dias_lista = str(vehiculo.dias_permitidos).lower()
        
        dias_nombres = {
            'lunes': 0, 'martes': 1, 'miercoles': 2, 'miércoles': 2,
            'jueves': 3, 'viernes': 4, 'sabado': 5, 'sábado': 5, 'domingo': 6
        }
        
        # Intentar parsear como números primero
        try:
            dias_permitidos = [int(d.strip()) for d in dias_lista.split(',')]
        except ValueError:
            # Si falla, intentar como nombres de días
            dias_permitidos = []
            for dia in dias_lista.split(','):
                dia = dia.strip()
                if dia in dias_nombres:
                    dias_permitidos.append(dias_nombres[dia])
        
        # Si el día actual no está en la lista de permitidos, denegar
        if dia_actual not in dias_permitidos:
            return False
    
    # Verificar horario
    if hora_actual < vehiculo.hora_inicio or hora_actual > vehiculo.hora_fin:
        return False
    
    return True

def procesar_deteccion_placa(datos, db: Session) -> dict:
    """
    Procesamiento centralizado con Saneamiento de Matrículas (No-Guion)
    """
    # 🧼 FILTRO DE SEGURIDAD INTERNA: Forzar mayúsculas, remover guiones y espacios en blanco
    placa = datos.placa.replace("-", "").replace(" ", "").upper()
    timestamp = datos.timestamp
    
    # Buscar vehículo por placa totalmente estandarizada
    vehiculo = db.query(Vehiculo).filter(Vehiculo.placa == placa).first()
    
    # Caso 1: Vehículo no registrado
    if not vehiculo:
        return {
            "estado": "DENEGADO",
            "mensaje": f"⛔ Vehículo DESCONOCIDO - Placa {placa} no registrada en el sistema",
            "placa": placa,
            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "propietario": None,
            "tipo_alerta": "vehiculo_no_registrado",
            "detalles": {
                "codigo": "UNKNOWN_VEHICLE",
                "accion_recomendada": "Verificar identificación del conductor"
            }
        }
    
    # Caso 2: Vehículo con acceso denegado permanentemente o inactivo
    if vehiculo.estado_acceso and vehiculo.estado_acceso.upper() in ["DENEGADO", "BLOQUEADO", "INACTIVO"]:
        return {
            "estado": "DENEGADO",
            "mensaje": f"⛔ ACCESO BLOQUEADO - Vehículo {placa} ({vehiculo.propietario}) tiene acceso restringido",
            "placa": placa,
            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "propietario": vehiculo.propietario,
            "tipo_alerta": "vehiculo_bloqueado",
            "detalles": {
                "codigo": "BLOCKED_VEHICLE",
                "estado": vehiculo.estado_acceso,
                "observacion": vehiculo.observacion,
                "accion_recomendada": "Notificar al superior y verificar motivo del bloqueo"
            }
        }
    
    # Caso 3: Verificar horarios y días permitidos
    ahora = datetime.now()
    dia_semana = ahora.weekday()  # 0=Lunes, 6=Domingo
    hora_actual = ahora.strftime("%H:%M")
    
    if verificar_horario_acceso(vehiculo, hora_actual, dia_semana):
        return {
            "estado": "PERMITIDO",
            "mensaje": f"✅ ACCESO PERMITIDO - Bienvenido {vehiculo.propietario}",
            "placa": placa,
            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "propietario": vehiculo.propietario,
            "tipo_alerta": "acceso_permitido",
            "detalles": {
                "codigo": "ACCESS_GRANTED",
                "vehiculo_id": vehiculo.id,
                "tipo_vehiculo": vehiculo.tipo_vehiculo,
                "color": vehiculo.color,
                "marca_modelo": vehiculo.marca_modelo,
                "mensaje_bienvenida": f"Acceso autorizado - {vehiculo.propietario}"
            }
        }
    else:
        # Caso 4: Acceso denegado por horario/día
        razon = []
        if vehiculo.dias_permitidos:
            razon.append(f"días permitidos: {vehiculo.dias_permitidos}")
        if vehiculo.hora_inicio and vehiculo.hora_fin:
            razon.append(f"horario: {vehiculo.hora_inicio} a {vehiculo.hora_fin}")
        
        razon_str = " y ".join(razon)
        
        return {
            "estado": "DENEGADO",
            "mensaje": f"⛔ ACCESO DENEGADO - Fuera de horario ({razon_str})",
            "placa": placa,
            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "propietario": vehiculo.propietario,
            "tipo_alerta": "fuera_horario",
            "detalles": {
                "codigo": "OUT_OF_SCHEDULE",
                "hora_actual": hora_actual,
                "dia_actual": dia_semana,
                "hora_inicio": vehiculo.hora_inicio,
                "hora_fin": vehiculo.hora_fin,
                "dias_permitidos": vehiculo.dias_permitidos,
                "accion_recomendada": "Solicitar autorización especial"
            }
        }

# Endpoint para procesamiento manual o desde el dashboard
@router.post("/api/lpr/procesar-manual", tags=["Control de Acceso"])
def procesar_placa_manual(
    placa: str,
    db: Session = Depends(get_db)
):
    """
    Endpoint para verificar manualmente una placa desde el dashboard
    """
    from backend_lpr.schemas.validaciones import DeteccionPlacaInput  # ✅ CORREGIDO
    
    datos = DeteccionPlacaInput(
        placa=placa,
        timestamp=datetime.now()
    )
    
    return procesar_deteccion_placa(datos, db)

# Endpoint para consultar historial de accesos
@router.get("/api/lpr/historial/{placa}", tags=["Control de Acceso"])
def consultar_historial_placa(
    placa: str,
    db: Session = Depends(get_db)
):
    # Aplicamos la misma limpieza en las búsquedas GET manuales
    placa_limpia = placa.replace("-", "").replace(" ", "").upper()
    vehiculo = db.query(Vehiculo).filter(Vehiculo.placa == placa_limpia).first()
    
    if not vehiculo:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró vehículo con placa {placa_limpia}"
        )
    
    return {
        "placa": vehiculo.placa,
        "propietario": vehiculo.propietario,
        "marca_modelo": vehiculo.marca_modelo,
        "color": vehiculo.color,
        "tipo_vehiculo": vehiculo.tipo_vehiculo,
        "estado_acceso": vehiculo.estado_acceso,
        "hora_inicio": vehiculo.hora_inicio,
        "hora_fin": vehiculo.hora_fin,
        "dias_permitidos": vehiculo.dias_permitidos,
        "observacion": vehiculo.observacion
    }

# Endpoint para estadísticas del dashboard
@router.get("/api/lpr/estadisticas", tags=["Control de Acceso"])
def obtener_estadisticas(db: Session = Depends(get_db)):
    total = db.query(Vehiculo).count()
    return {
        "total_vehiculos_registrados": total,
        "accesos_hoy": 0,
        "denegados_hoy": 0,
        "ultima_deteccion": None
    }