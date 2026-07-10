"""
Controlador de Acceso - Sistema AEGIS LPR
Maneja la detección de placas, verificación de acceso e historial.
"""
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
import io
import base64
import re

router = APIRouter()

MODELO_PATH = 'best.pt'
modelo_yolo = YOLO(MODELO_PATH)

# PyTesseract - más ligero que EasyOCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\MI PC PERSONAL\Desktop\Tesseract-OCR\tesseract.exe'

def verificar_horario_acceso(vehiculo, hora_actual, dia_actual: int) -> bool:
    """Verifica si un vehículo tiene permiso de acceso en el día y hora actual."""
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
    """Guarda un registro de acceso en la base de datos."""
    try:
        ultimo = db.query(RegistroAcceso).order_by(RegistroAcceso.id_registro.desc()).first()
        if ultimo and ultimo.placa_leida == placa:
            if datetime.now() - ultimo.fecha_hora < timedelta(seconds=10):
                return
        registro = RegistroAcceso(placa_leida=placa, estado_acceso=estado, motivo_denegacion=motivo)
        db.add(registro)
        db.commit()
    except Exception as e:
        print(f"[ERROR] [{datetime.now()}]: No se pudo guardar el registro - {str(e)}")

def mejorar_imagen_ocr(recorte):
    """Mejora la calidad de un recorte de imagen para OCR."""
    if recorte is None or recorte.size == 0:
        return recorte
    gris = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
    gris = cv2.equalizeHist(gris)
    gris = cv2.resize(gris, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    _, gris = cv2.threshold(gris, 90, 255, cv2.THRESH_BINARY)
    return gris

def extraer_placa_venezolana(texto_completo):
    """Extrae el número de placa venezolana de un texto largo."""
    patrones = re.findall(r'[A-Z]{2,4}[0-9]{2,3}[A-Z]{0,2}', texto_completo)
    patrones_validos = [p for p in patrones if len(re.findall(r'[0-9]', p)) >= 2]
    if patrones_validos:
        texto = max(patrones_validos, key=len)
        if len(texto) > 7: texto = texto[-7:]
        return texto
    texto_limpio = re.sub(r'[^A-Z0-9]', '', texto_completo)
    if len(texto_limpio) >= 5:
        return texto_limpio[-7:] if len(texto_limpio) > 7 else texto_limpio
    return None

def leer_placa_imagen(imagen_bytes):
    """Detecta y lee una placa vehicular desde una imagen. YOLO + PyTesseract."""
    try:
        nparr = np.frombuffer(imagen_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            print(f"[ERROR] [{datetime.now()}]: No se pudo decodificar la imagen")
            return None, 0, None
        
        img_resultado = img.copy()
        results = modelo_yolo(img, verbose=False)[0]
        placa_detectada = None
        confianza_final = 0
        
        if results.boxes is not None and len(results.boxes) > 0:
            for box in results.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                if conf < 0.25: continue
                
                cv2.rectangle(img_resultado, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img_resultado, f"PLACA ({conf*100:.0f}%)", (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                recorte = img[y1:y2, x1:x2]
                recorte = mejorar_imagen_ocr(recorte)
                
                texto_completo = pytesseract.image_to_string(recorte, config='--psm 7').upper().strip()
                texto_placa = extraer_placa_venezolana(texto_completo)
                
                if texto_placa:
                    print(f"   🔤 OCR leyó: {texto_placa}")
                    placa_detectada = texto_placa
                    confianza_final = conf
                    break
        
        if not placa_detectada:
            gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            texto_completo = pytesseract.image_to_string(gris, config='--psm 6').upper().strip()
            texto_placa = extraer_placa_venezolana(texto_completo)
            if texto_placa:
                placa_detectada = texto_placa
                confianza_final = 0.5
        
        _, buffer = cv2.imencode('.jpg', img_resultado)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        return placa_detectada, confianza_final, img_base64
        
    except Exception as e:
        print(f"[ERROR] [{datetime.now()}]: Error en lectura de placa - {str(e)}")
        return None, 0, None

def procesar_deteccion_placa(datos, db: Session) -> dict:
    """Procesa una detección de placa y determina si el acceso es permitido."""
    try:
        placa = datos.placa.replace("-", "").replace(" ", "").upper()
        timestamp = datos.timestamp
        vehiculo = db.query(Vehiculo).filter(Vehiculo.placa == placa).first()
        
        if not vehiculo:
            resultado = {
                "estado": "DENEGADO", "mensaje": f"⛔ Vehiculo DESCONOCIDO - Placa {placa} no registrada",
                "placa": placa, "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                "propietario": None, "tipo_alerta": "vehiculo_no_registrado"
            }
            guardar_registro(db, placa, "DENEGADO", resultado["mensaje"])
            return resultado
        
        if vehiculo.estado_acceso and vehiculo.estado_acceso.upper() in ["DENEGADO", "BLOQUEADO", "INACTIVO"]:
            motivo = f"⛔ ACCESO BLOQUEADO - {vehiculo.propietario}"
            if vehiculo.observacion: motivo += f" - {vehiculo.observacion}"
            resultado = {
                "estado": "DENEGADO", "mensaje": motivo,
                "placa": placa, "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                "propietario": vehiculo.propietario, "tipo_alerta": "vehiculo_bloqueado"
            }
            guardar_registro(db, placa, "DENEGADO", motivo)
            return resultado
        
        ahora = datetime.now()
        dia_semana = ahora.weekday()
        hora_actual = ahora.time()
        
        if verificar_horario_acceso(vehiculo, hora_actual, dia_semana):
            resultado = {
                "estado": "PERMITIDO", "mensaje": f"✅ ACCESO PERMITIDO - Bienvenido {vehiculo.propietario}",
                "placa": placa, "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                "propietario": vehiculo.propietario, "tipo_alerta": "acceso_permitido"
            }
            guardar_registro(db, placa, "PERMITIDO", resultado["mensaje"])
            return resultado
        else:
            razon = []
            if vehiculo.dias_permitidos: razon.append(f"dias permitidos: {vehiculo.dias_permitidos}")
            if vehiculo.hora_inicio and vehiculo.hora_fin: razon.append(f"horario: {vehiculo.hora_inicio} a {vehiculo.hora_fin}")
            razon_str = " y ".join(razon)
            resultado = {
                "estado": "DENEGADO", "mensaje": f"⛔ ACCESO DENEGADO - Fuera de horario ({razon_str})",
                "placa": placa, "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                "propietario": vehiculo.propietario, "tipo_alerta": "fuera_horario"
            }
            guardar_registro(db, placa, "DENEGADO", resultado["mensaje"])
            return resultado
    except Exception as e:
        print(f"[ERROR] [{datetime.now()}]: Error procesando deteccion - {str(e)}")
        return {"estado": "ERROR", "mensaje": f"Error interno", "placa": datos.placa,
                "timestamp": str(datetime.now()), "propietario": None, "tipo_alerta": "error_sistema"}


@router.post("/api/lpr/procesar-imagen", tags=["Control de Acceso"])
async def procesar_imagen_subida(
    file: UploadFile = File(None),
    placa_manual: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Endpoint para procesar una imagen de placa o una placa manual."""
    placa_detectada = None
    confianza = 0
    imagen_base64 = None
    
    if placa_manual:
        placa_detectada = placa_manual.upper().strip()
        confianza = 1.0
    elif file:
        contents = await file.read()
        placa_detectada, confianza, imagen_base64 = leer_placa_imagen(contents)
    
    if not placa_detectada:
        raise HTTPException(status_code=400, detail="No se pudo leer la placa. Intente manualmente.")
    
    from backend_lpr.schemas.validaciones import DeteccionPlacaInput
    datos = DeteccionPlacaInput(placa=placa_detectada, timestamp=datetime.now(), confianza=round(confianza, 2), origen="imagen_subida")
    resultado = procesar_deteccion_placa(datos, db)
    if imagen_base64:
        resultado["imagen_procesada"] = f"data:image/jpeg;base64,{imagen_base64}"
    return resultado


@router.get("/api/lpr/historial", tags=["Control de Acceso"])
def obtener_historial(
    desde: Optional[str] = None, hasta: Optional[str] = None,
    estado: Optional[str] = None, placa: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Obtiene el historial de accesos con filtros opcionales."""
    query = db.query(RegistroAcceso)
    if desde: query = query.filter(RegistroAcceso.fecha_hora >= datetime.fromisoformat(desde))
    if hasta: query = query.filter(RegistroAcceso.fecha_hora <= datetime.fromisoformat(hasta))
    if estado: query = query.filter(RegistroAcceso.estado_acceso == estado.upper())
    if placa: query = query.filter(RegistroAcceso.placa_leida.ilike(f"%{placa}%"))
    registros = query.order_by(RegistroAcceso.fecha_hora.desc()).limit(100).all()
    return {
        "total": len(registros),
        "registros": [{"id": r.id_registro, "placa": r.placa_leida, "fecha_hora": r.fecha_hora.isoformat() if r.fecha_hora else None,
                        "estado": r.estado_acceso, "motivo": r.motivo_denegacion} for r in registros]
    }


@router.post("/api/lpr/procesar-manual", tags=["Control de Acceso"])
def procesar_placa_manual(placa: str, db: Session = Depends(get_db)):
    """Procesa una placa ingresada manualmente por el operador."""
    from backend_lpr.schemas.validaciones import DeteccionPlacaInput
    datos = DeteccionPlacaInput(placa=placa, timestamp=datetime.now())
    return procesar_deteccion_placa(datos, db)


@router.get("/api/lpr/estadisticas", tags=["Control de Acceso"])
def obtener_estadisticas(db: Session = Depends(get_db)):
    """Obtiene estadísticas generales del sistema."""
    total_vehiculos = db.query(Vehiculo).count()
    total_registros = db.query(RegistroAcceso).count()
    denegados = db.query(RegistroAcceso).filter(RegistroAcceso.estado_acceso == "DENEGADO").count()
    return {"total_vehiculos_registrados": total_vehiculos, "total_accesos_registrados": total_registros,
            "denegados": denegados, "ultima_deteccion": None}