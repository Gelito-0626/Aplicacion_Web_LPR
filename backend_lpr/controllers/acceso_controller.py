from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from backend_lpr.config import get_db
from backend_lpr.models.tablas import Vehiculo, RegistroAcceso
import cv2
import numpy as np
import pytesseract
from ultralytics import YOLO
from PIL import Image, ImageEnhance, ImageFilter
import io

router = APIRouter()

MODELO_PATH = 'best.pt'
modelo_yolo = YOLO(MODELO_PATH)

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\MI PC PERSONAL\Desktop\Tesseract-OCR\tesseract.exe'

def verificar_horario_acceso(vehiculo, hora_actual, dia_actual: int) -> bool:
    if not vehiculo.hora_inicio or not vehiculo.hora_fin:
        return True
    
    if vehiculo.dias_permitidos:
        dias_lista = str(vehiculo.dias_permitidos).lower()
        dias_nombres = {
            'lunes': 0, 'martes': 1, 'miercoles': 2, 'miércoles': 2,
            'jueves': 3, 'viernes': 4, 'sabado': 5, 'sábado': 5, 'domingo': 6
        }
        try:
            dias_permitidos = [int(d.strip()) for d in dias_lista.split(',')]
        except ValueError:
            dias_permitidos = []
            for dia in dias_lista.split(','):
                dia = dia.strip()
                if dia in dias_nombres:
                    dias_permitidos.append(dias_nombres[dia])
        if dia_actual not in dias_permitidos:
            return False
    
    if hora_actual < vehiculo.hora_inicio or hora_actual > vehiculo.hora_fin:
        return False
    
    return True

def guardar_registro(db: Session, placa: str, estado: str, motivo: str):
    ultimo = db.query(RegistroAcceso).order_by(RegistroAcceso.id_registro.desc()).first()
    
    if ultimo and ultimo.placa_leida == placa:
        if datetime.now() - ultimo.fecha_hora < timedelta(seconds=10):
            return
    
    registro = RegistroAcceso(
        placa_leida=placa,
        estado_acceso=estado,
        motivo_denegacion=motivo
    )
    db.add(registro)
    db.commit()

def mejorar_imagen_ocr(recorte):
    if recorte is None or recorte.size == 0:
        return recorte
    gris = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
    gris = cv2.equalizeHist(gris)
    gris = cv2.resize(gris, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
    _, gris = cv2.threshold(gris, 90, 255, cv2.THRESH_BINARY)
    return gris

def preprocesar_imagen(imagen_bytes):
    """Mejora la imagen con PIL antes de YOLO"""
    pil_img = Image.open(io.BytesIO(imagen_bytes))
    pil_img = pil_img.convert('L')
    enhancer = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer.enhance(2.5)
    pil_img = pil_img.filter(ImageFilter.SHARPEN)
    img = np.array(pil_img)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img

def leer_placa_imagen(imagen_bytes):
    # Preprocesar con PIL
    img = preprocesar_imagen(imagen_bytes)
    
    results = modelo_yolo(img, verbose=False)[0]
    
    if results.boxes is not None and len(results.boxes) > 0:
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0])
            
            if conf < 0.25:
                continue
            
            recorte = img[y1:y2, x1:x2]
            recorte = mejorar_imagen_ocr(recorte)
            
            # Probar múltiples configuraciones de PSM
            for psm in ['8', '7', '6']:
                texto = pytesseract.image_to_string(
                    recorte,
                    config=f'--psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                )
                texto = texto.strip().upper().replace(" ", "").replace("\n", "")
                if texto and len(texto) >= 4:
                    return texto, conf
    
    # Fallback: OCR en imagen completa
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    for psm in ['8', '7', '6']:
        texto = pytesseract.image_to_string(
            gris, 
            config=f'--psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        )
        texto = texto.strip().upper().replace(" ", "").replace("\n", "")
        if texto and len(texto) >= 4:
            return texto, 0.5
    
    return None, 0

def procesar_deteccion_placa(datos, db: Session) -> dict:
    placa = datos.placa.replace("-", "").replace(" ", "").upper()
    timestamp = datos.timestamp
    
    vehiculo = db.query(Vehiculo).filter(Vehiculo.placa == placa).first()
    
    if not vehiculo:
        resultado = {
            "estado": "DENEGADO",
            "mensaje": f"⛔ Vehiculo DESCONOCIDO - Placa {placa} no registrada",
            "placa": placa,
            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "propietario": None,
            "tipo_alerta": "vehiculo_no_registrado"
        }
        guardar_registro(db, placa, "DENEGADO", resultado["mensaje"])
        return resultado
    
    if vehiculo.estado_acceso and vehiculo.estado_acceso.upper() in ["DENEGADO", "BLOQUEADO", "INACTIVO"]:
        motivo = f"⛔ ACCESO BLOQUEADO - {vehiculo.propietario}" + (f" - {vehiculo.observacion}" if vehiculo.observacion else "")
        resultado = {
            "estado": "DENEGADO",
            "mensaje": motivo,
            "placa": placa,
            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "propietario": vehiculo.propietario,
            "tipo_alerta": "vehiculo_bloqueado"
        }
        guardar_registro(db, placa, "DENEGADO", motivo)
        return resultado
    
    ahora = datetime.now()
    dia_semana = ahora.weekday()
    hora_actual = ahora.time()
    
    if verificar_horario_acceso(vehiculo, hora_actual, dia_semana):
        resultado = {
            "estado": "PERMITIDO",
            "mensaje": f"✅ ACCESO PERMITIDO - Bienvenido {vehiculo.propietario}",
            "placa": placa,
            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "propietario": vehiculo.propietario,
            "tipo_alerta": "acceso_permitido"
        }
        guardar_registro(db, placa, "PERMITIDO", resultado["mensaje"])
        return resultado
    else:
        razon = []
        if vehiculo.dias_permitidos:
            razon.append(f"dias permitidos: {vehiculo.dias_permitidos}")
        if vehiculo.hora_inicio and vehiculo.hora_fin:
            razon.append(f"horario: {vehiculo.hora_inicio} a {vehiculo.hora_fin}")
        razon_str = " y ".join(razon)
        
        resultado = {
            "estado": "DENEGADO",
            "mensaje": f"⛔ ACCESO DENEGADO - Fuera de horario ({razon_str})",
            "placa": placa,
            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "propietario": vehiculo.propietario,
            "tipo_alerta": "fuera_horario"
        }
        guardar_registro(db, placa, "DENEGADO", resultado["mensaje"])
        return resultado


@router.post("/api/lpr/procesar-imagen", tags=["Control de Acceso"])
async def procesar_imagen_subida(
    file: UploadFile = File(None),
    placa_manual: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    placa_detectada = None
    confianza = 0
    
    if placa_manual:
        placa_detectada = placa_manual.upper().strip()
        confianza = 1.0
    elif file:
        contents = await file.read()
        placa_detectada, confianza = leer_placa_imagen(contents)
    
    if not placa_detectada:
        raise HTTPException(status_code=400, detail="No se pudo leer la placa. Intente manualmente.")
    
    from backend_lpr.schemas.validaciones import DeteccionPlacaInput
    datos = DeteccionPlacaInput(
        placa=placa_detectada,
        timestamp=datetime.now(),
        confianza=round(confianza, 2),
        origen="imagen_subida"
    )
    
    return procesar_deteccion_placa(datos, db)


@router.get("/api/lpr/historial", tags=["Control de Acceso"])
def obtener_historial(
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    estado: Optional[str] = None,
    placa: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(RegistroAcceso)
    
    if desde:
        query = query.filter(RegistroAcceso.fecha_hora >= datetime.fromisoformat(desde))
    if hasta:
        query = query.filter(RegistroAcceso.fecha_hora <= datetime.fromisoformat(hasta))
    if estado:
        query = query.filter(RegistroAcceso.estado_acceso == estado.upper())
    if placa:
        query = query.filter(RegistroAcceso.placa_leida.ilike(f"%{placa}%"))
    
    registros = query.order_by(RegistroAcceso.fecha_hora.desc()).limit(100).all()
    
    return {
        "total": len(registros),
        "registros": [
            {
                "id": r.id_registro,
                "placa": r.placa_leida,
                "fecha_hora": r.fecha_hora.isoformat() if r.fecha_hora else None,
                "estado": r.estado_acceso,
                "motivo": r.motivo_denegacion
            }
            for r in registros
        ]
    }


@router.post("/api/lpr/procesar-manual", tags=["Control de Acceso"])
def procesar_placa_manual(placa: str, db: Session = Depends(get_db)):
    from backend_lpr.schemas.validaciones import DeteccionPlacaInput
    datos = DeteccionPlacaInput(placa=placa, timestamp=datetime.now())
    return procesar_deteccion_placa(datos, db)


@router.get("/api/lpr/estadisticas", tags=["Control de Acceso"])
def obtener_estadisticas(db: Session = Depends(get_db)):
    total_vehiculos = db.query(Vehiculo).count()
    total_registros = db.query(RegistroAcceso).count()
    denegados = db.query(RegistroAcceso).filter(RegistroAcceso.estado_acceso == "DENEGADO").count()
    return {
        "total_vehiculos_registrados": total_vehiculos,
        "total_accesos_registrados": total_registros,
        "denegados": denegados,
        "ultima_deteccion": None
    }