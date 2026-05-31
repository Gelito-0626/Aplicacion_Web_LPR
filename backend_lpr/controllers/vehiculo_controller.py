from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend_lpr.config import get_db
from backend_lpr.models.tablas import Vehiculo
from backend_lpr.schemas.validaciones import VehiculoCreate, VehiculoUpdate, VehiculoResponse

router = APIRouter(prefix="/api/vehiculos", tags=["Gestión de Vehículos"])

# --- ENDPOINTS CRUD PARA VEHÍCULOS ---

@router.post("/registro")
def registrar_vehiculo(datos: VehiculoCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo vehículo en el sistema con control de acceso horario
    """
    
    # 🔥 Forzamos la placa a mayúsculas para evitar fallos de coincidencia con la IA
    placa_mayuscula = datos.placa.upper().strip()
    
    # Validar formato de placa (4 letras + 3 números para formato bolivariano)
    if len(placa_mayuscula) != 7:
        raise HTTPException(
            status_code=400, 
            detail="La placa debe tener exactamente 7 caracteres (4 letras + 3 números)"
        )
    
    if not placa_mayuscula[:4].isalpha() or not placa_mayuscula[4:].isdigit():
        raise HTTPException(
            status_code=400, 
            detail="Formato de placa inválido. Debe ser: ABCD123"
        )
    
    # Revisa duplicados
    v = db.query(Vehiculo).filter_by(placa=placa_mayuscula).first()
    if v:
        raise HTTPException(
            status_code=400, 
            detail=f"⚠️ Ya existe un vehículo registrado con la placa {placa_mayuscula}"
        )
    
    # Validar estado_acceso
    estado = datos.estado_acceso.upper() if datos.estado_acceso else "PERMITIDO"
    if estado not in ["PERMITIDO", "DENEGADO", "BLOQUEADO", "INACTIVO"]:
        raise HTTPException(
            status_code=400,
            detail=f"Estado de acceso inválido: {estado}. Use: PERMITIDO, DENEGADO, BLOQUEADO o INACTIVO"
        )
    
    # Crea y guarda el vehículo
    nuevo = Vehiculo(
        placa=placa_mayuscula,
        propietario=datos.propietario.strip(),
        marca_modelo=datos.marca_modelo.strip() if datos.marca_modelo else None,
        color=datos.color.strip() if datos.color else None,
        tipo_vehiculo=datos.tipo_vehiculo.strip() if datos.tipo_vehiculo else None,
        estado_acceso=estado,
        observacion=datos.observacion.strip() if datos.observacion else None,
        hora_inicio=datos.hora_inicio,
        hora_fin=datos.hora_fin,
        dias_permitidos=datos.dias_permitidos.strip() if datos.dias_permitidos else None
    )
    
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    
    return {
        "registro": True,
        "motivo": "✅ Vehículo registrado exitosamente",
        "datos": {
            "id": nuevo.id,
            "placa": nuevo.placa,
            "propietario": nuevo.propietario,
            "marca_modelo": nuevo.marca_modelo,
            "color": nuevo.color,
            "tipo_vehiculo": nuevo.tipo_vehiculo,
            "estado_acceso": nuevo.estado_acceso,
            "hora_inicio": nuevo.hora_inicio,
            "hora_fin": nuevo.hora_fin,
            "dias_permitidos": nuevo.dias_permitidos,
            "observacion": nuevo.observacion
        }
    }


@router.get("/listar")
def listar_vehiculos(
    skip: int = Query(0, description="Saltar N registros"),
    limit: int = Query(100, description="Límite de registros"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    busqueda: Optional[str] = Query(None, description="Buscar por placa o propietario"),
    db: Session = Depends(get_db)
):
    """Lista todos los vehículos registrados con filtros opcionales"""
    query = db.query(Vehiculo)
    
    if estado:
        query = query.filter(Vehiculo.estado_acceso == estado.upper())
    
    if busqueda:
        busqueda = f"%{busqueda}%"
        query = query.filter(
            (Vehiculo.placa.ilike(busqueda)) | 
            (Vehiculo.propietario.ilike(busqueda))
        )
    
    vehiculos = query.order_by(Vehiculo.placa).offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "total": total,
        "vehiculos": [
            {
                "id": v.id,
                "placa": v.placa,
                "propietario": v.propietario,
                "marca_modelo": v.marca_modelo,
                "color": v.color,
                "tipo_vehiculo": v.tipo_vehiculo,
                "estado_acceso": v.estado_acceso,
                "hora_inicio": v.hora_inicio,
                "hora_fin": v.hora_fin,
                "dias_permitidos": v.dias_permitidos,
                "observacion": v.observacion
            }
            for v in vehiculos
        ]
    }


@router.get("/buscar/{placa}")
def buscar_por_placa(placa: str, db: Session = Depends(get_db)):
    """Busca un vehículo específico por su número de placa"""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.placa == placa.upper().strip()).first()
    
    if not vehiculo:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ningún vehículo con placa {placa}"
        )
    
    return {
        "id": vehiculo.id,
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


@router.put("/actualizar/{vehiculo_id}")
def actualizar_vehiculo(
    vehiculo_id: int, 
    datos: VehiculoUpdate, 
    db: Session = Depends(get_db)
):
    """Actualiza la información de un vehículo existente"""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    
    if not vehiculo:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró vehículo con ID {vehiculo_id}"
        )
    
    if datos.propietario is not None:
        vehiculo.propietario = datos.propietario.strip()
    if datos.marca_modelo is not None:
        vehiculo.marca_modelo = datos.marca_modelo.strip()
    if datos.color is not None:
        vehiculo.color = datos.color.strip()
    if datos.tipo_vehiculo is not None:
        vehiculo.tipo_vehiculo = datos.tipo_vehiculo.strip()
    if datos.estado_acceso is not None:
        estado = datos.estado_acceso.upper()
        if estado not in ["PERMITIDO", "DENEGADO", "BLOQUEADO", "INACTIVO"]:
            raise HTTPException(status_code=400, detail=f"Estado inválido: {estado}")
        vehiculo.estado_acceso = estado
    if datos.hora_inicio is not None:
        vehiculo.hora_inicio = datos.hora_inicio
    if datos.hora_fin is not None:
        vehiculo.hora_fin = datos.hora_fin
    if datos.dias_permitidos is not None:
        vehiculo.dias_permitidos = datos.dias_permitidos.strip()
    if datos.observacion is not None:
        vehiculo.observacion = datos.observacion.strip()
    
    db.commit()
    db.refresh(vehiculo)
    
    return {
        "actualizado": True,
        "motivo": "✅ Vehículo actualizado exitosamente",
        "datos": {
            "id": vehiculo.id,
            "placa": vehiculo.placa,
            "propietario": vehiculo.propietario,
            "estado_acceso": vehiculo.estado_acceso,
            "hora_inicio": vehiculo.hora_inicio,
            "hora_fin": vehiculo.hora_fin,
            "dias_permitidos": vehiculo.dias_permitidos
        }
    }


@router.delete("/eliminar/{vehiculo_id}")
def eliminar_vehiculo(vehiculo_id: int, db: Session = Depends(get_db)):
    """Elimina un vehículo del sistema"""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    
    if not vehiculo:
        raise HTTPException(status_code=404, detail=f"No se encontró vehículo con ID {vehiculo_id}")
    
    placa = vehiculo.placa
    propietario = vehiculo.propietario
    
    db.delete(vehiculo)
    db.commit()
    
    return {
        "eliminado": True,
        "motivo": f"✅ Vehículo {placa} ({propietario}) eliminado exitosamente"
    }


@router.patch("/cambiar-estado/{vehiculo_id}")
def cambiar_estado_vehiculo(
    vehiculo_id: int,
    nuevo_estado: str = Query(..., description="Nuevo estado: PERMITIDO, DENEGADO, BLOQUEADO"),
    db: Session = Depends(get_db)
):
    """Cambia rápidamente el estado de acceso de un vehículo"""
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    
    if not vehiculo:
        raise HTTPException(status_code=404, detail=f"No se encontró vehículo con ID {vehiculo_id}")
    
    estado = nuevo_estado.upper()
    if estado not in ["PERMITIDO", "DENEGADO", "BLOQUEADO", "INACTIVO"]:
        raise HTTPException(status_code=400, detail=f"Estado inválido: {estado}")
    
    estado_anterior = vehiculo.estado_acceso
    vehiculo.estado_acceso = estado
    
    db.commit()
    db.refresh(vehiculo)
    
    return {
        "actualizado": True,
        "motivo": f"✅ Estado de {vehiculo.placa} cambiado de {estado_anterior} a {estado}",
        "datos": {
            "id": vehiculo.id,
            "placa": vehiculo.placa,
            "propietario": vehiculo.propietario,
            "estado_anterior": estado_anterior,
            "estado_nuevo": estado
        }
    }