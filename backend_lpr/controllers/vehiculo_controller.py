from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend_lpr.config import get_db
from backend_lpr.models.tablas import Vehiculo
from backend_lpr.schemas.validaciones import VehiculoCreate, VehiculoUpdate, VehiculoResponse

router = APIRouter(prefix="/api/vehiculos", tags=["Gestión de Vehículos"])

@router.post("/registro")
def registrar_vehiculo(datos: VehiculoCreate, db: Session = Depends(get_db)):
    placa_mayuscula = datos.placa.upper().strip()
    
    if len(placa_mayuscula) < 4 or len(placa_mayuscula) > 15:
        raise HTTPException(status_code=400, detail="La placa debe tener entre 4 y 15 caracteres")
    
    if not placa_mayuscula.isalnum():
        raise HTTPException(status_code=400, detail="La placa solo debe contener letras y números")
    
    v = db.query(Vehiculo).filter_by(placa=placa_mayuscula).first()
    if v:
        raise HTTPException(status_code=400, detail=f"Ya existe un vehiculo con la placa {placa_mayuscula}")
    
    estado = datos.estado_acceso.upper() if datos.estado_acceso else "PERMITIDO"
    if estado not in ["PERMITIDO", "DENEGADO", "BLOQUEADO", "INACTIVO"]:
        raise HTTPException(status_code=400, detail=f"Estado invalido: {estado}")
    
    from datetime import datetime as dt
    h_inicio = dt.strptime(datos.hora_inicio, "%H:%M").time() if datos.hora_inicio else dt.strptime("00:00", "%H:%M").time()
    h_fin = dt.strptime(datos.hora_fin, "%H:%M").time() if datos.hora_fin else dt.strptime("23:59", "%H:%M").time()

    nuevo = Vehiculo(
        placa=placa_mayuscula,
        propietario=datos.propietario.strip(),
        marca_modelo=datos.marca_modelo.strip() if datos.marca_modelo else None,
        color=datos.color.strip() if datos.color else None,
        tipo_vehiculo=datos.tipo_vehiculo.strip() if datos.tipo_vehiculo else None,
        estado_acceso=estado,
        observacion=datos.observacion.strip() if datos.observacion else None,
        hora_inicio=h_inicio,
        hora_fin=h_fin,
        dias_permitidos=datos.dias_permitidos.strip() if datos.dias_permitidos else None
    )
    
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    
    return {
        "registro": True,
        "motivo": "Vehiculo registrado exitosamente",
        "datos": {
            "placa": nuevo.placa,
            "propietario": nuevo.propietario,
            "marca_modelo": nuevo.marca_modelo,
            "color": nuevo.color,
            "tipo_vehiculo": nuevo.tipo_vehiculo,
            "estado_acceso": nuevo.estado_acceso,
            "observacion": nuevo.observacion,
            "hora_inicio": str(nuevo.hora_inicio) if nuevo.hora_inicio else None,
            "hora_fin": str(nuevo.hora_fin) if nuevo.hora_fin else None,
            "dias_permitidos": nuevo.dias_permitidos
        }
    }


@router.get("/listar")
def listar_vehiculos(
    skip: int = Query(0),
    limit: int = Query(100),
    estado: Optional[str] = Query(None),
    busqueda: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Vehiculo)
    if estado:
        query = query.filter(Vehiculo.estado_acceso == estado.upper())
    if busqueda:
        b = f"%{busqueda}%"
        query = query.filter((Vehiculo.placa.ilike(b)) | (Vehiculo.propietario.ilike(b)))
    
    vehiculos = query.order_by(Vehiculo.placa).offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "total": total,
        "vehiculos": [
            {
                "placa": v.placa,
                "propietario": v.propietario,
                "marca_modelo": v.marca_modelo,
                "color": v.color,
                "tipo_vehiculo": v.tipo_vehiculo,
                "estado_acceso": v.estado_acceso,
                "observacion": v.observacion,
                "hora_inicio": str(v.hora_inicio) if v.hora_inicio else None,
                "hora_fin": str(v.hora_fin) if v.hora_fin else None,
                "dias_permitidos": v.dias_permitidos
            }
            for v in vehiculos
        ]
    }


@router.get("/buscar/{placa}")
def buscar_por_placa(placa: str, db: Session = Depends(get_db)):
    vehiculo = db.query(Vehiculo).filter(Vehiculo.placa == placa.upper().strip()).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail=f"No se encontro vehiculo con placa {placa}")
    return {
        "placa": vehiculo.placa,
        "propietario": vehiculo.propietario,
        "marca_modelo": vehiculo.marca_modelo,
        "color": vehiculo.color,
        "tipo_vehiculo": vehiculo.tipo_vehiculo,
        "estado_acceso": vehiculo.estado_acceso,
        "observacion": vehiculo.observacion,
        "hora_inicio": str(vehiculo.hora_inicio) if vehiculo.hora_inicio else None,
        "hora_fin": str(vehiculo.hora_fin) if vehiculo.hora_fin else None,
        "dias_permitidos": vehiculo.dias_permitidos
    }


@router.put("/actualizar/{placa}")
def actualizar_vehiculo(placa: str, datos: VehiculoUpdate, db: Session = Depends(get_db)):
    vehiculo = db.query(Vehiculo).filter(Vehiculo.placa == placa.upper().strip()).first()
    
    if not vehiculo:
        raise HTTPException(status_code=404, detail=f"No se encontro vehiculo con placa {placa}")
    
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
            raise HTTPException(status_code=400, detail=f"Estado invalido: {estado}")
        vehiculo.estado_acceso = estado
    if datos.observacion is not None:
        vehiculo.observacion = datos.observacion.strip()
    if datos.hora_inicio is not None:
        from datetime import datetime as dt
        vehiculo.hora_inicio = dt.strptime(datos.hora_inicio, "%H:%M").time()
    if datos.hora_fin is not None:
        from datetime import datetime as dt
        vehiculo.hora_fin = dt.strptime(datos.hora_fin, "%H:%M").time()
    if datos.dias_permitidos is not None:
        vehiculo.dias_permitidos = datos.dias_permitidos.strip()
    
    db.commit()
    db.refresh(vehiculo)
    
    return {
        "actualizado": True,
        "motivo": "Vehiculo actualizado exitosamente",
        "datos": {
            "placa": vehiculo.placa,
            "propietario": vehiculo.propietario,
            "estado_acceso": vehiculo.estado_acceso,
            "observacion": vehiculo.observacion
        }
    }


@router.delete("/eliminar/{placa}")
def eliminar_vehiculo(placa: str, db: Session = Depends(get_db)):
    vehiculo = db.query(Vehiculo).filter(Vehiculo.placa == placa.upper().strip()).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail=f"No se encontro vehiculo con placa {placa}")
    db.delete(vehiculo)
    db.commit()
    return {"eliminado": True, "motivo": f"Vehiculo {placa} eliminado exitosamente"}