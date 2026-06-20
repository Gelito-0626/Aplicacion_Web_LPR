# Agente_LPR.py - 2026 - Optimizado para laptop
import cv2
import time
import requests
from datetime import datetime
from ultralytics import YOLO
import pytesseract
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\MI PC PERSONAL\Desktop\Tesseract-OCR\tesseract.exe'

MODELO_PATH = 'best.pt'
INTERVALO_CAPTURA = 4.0
BACKEND_URL = 'http://localhost:8000/api/lpr/deteccion'

COLOR_VERDE = (0, 255, 0)
COLOR_ROJO = (0, 0, 255)
FUENTE = cv2.FONT_HERSHEY_SIMPLEX

ultima_placa = ""
ultimo_envio = 0
INTERVALO_ENVIO = 8.0

def mejorar_imagen(recorte):
    if recorte is None or recorte.size == 0:
        return recorte
    gris = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
    gris = cv2.equalizeHist(gris)
    gris = cv2.resize(gris, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    _, gris = cv2.threshold(gris, 100, 255, cv2.THRESH_BINARY)
    return gris

def main():
    global ultima_placa, ultimo_envio
    
    print("🔄 Cargando modelo YOLO...")
    model = YOLO(MODELO_PATH)
    print("✅ Listo")

    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara")
        return

    print("✅ Cámara lista. Procesando...")
    
    last_capture = 0
    resultado_texto = ""
    estado = None

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.5)
            continue

        frame = cv2.flip(frame, 1)
        ahora = time.time()

        if ahora - last_capture >= INTERVALO_CAPTURA:
            last_capture = ahora
            print("📸 Capturando...")
            
            results = model(frame, verbose=False)[0]
            placa_detectada = None

            if results.boxes is not None and len(results.boxes) > 0:
                for box in results.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    conf = float(box.conf[0])
                    
                    if conf < 0.3:
                        continue
                    
                    recorte = frame[y1:y2, x1:x2]
                    recorte_mejorado = mejorar_imagen(recorte)
                    
                    try:
                        texto = pytesseract.image_to_string(
                            recorte_mejorado,
                            config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                        )
                        texto = texto.strip().upper().replace(" ", "").replace("\n", "")
                        if texto and len(texto) >= 4:
                            placa_detectada = texto
                            print(f"   🔤 Leído: {placa_detectada}")
                            
                            cv2.rectangle(frame, (x1, y1), (x2, y2), COLOR_VERDE, 2)
                            cv2.putText(frame, placa_detectada, (x1, y1-10), FUENTE, 0.7, COLOR_VERDE, 2)
                            break
                    except:
                        pass
            
            if placa_detectada:
                resultado_texto = placa_detectada
                
                if placa_detectada != ultima_placa or (ahora - ultimo_envio) > INTERVALO_ENVIO:
                    try:
                        r = requests.post(BACKEND_URL, json={
                            "placa": placa_detectada,
                            "timestamp": datetime.now().isoformat(),
                            "confianza": round(conf, 2),
                            "origen": "camara_principal"
                        }, timeout=3)
                        if r.status_code == 200:
                            res = r.json()
                            estado = res.get('estado', '?')
                            print(f"📤 Dashboard: {placa_detectada} → {estado}")
                            ultima_placa = placa_detectada
                            ultimo_envio = ahora
                    except Exception as e:
                        print(f"❌ Sin conexión: {e}")
            else:
                resultado_texto = "No detectado"
                print("   ⚠️ No se detectó placa")

        cv2.putText(frame, f"Lectura: {resultado_texto}", (10, 30), FUENTE, 0.7, COLOR_VERDE, 2)
        cv2.putText(frame, f"Prox: {max(0, INTERVALO_CAPTURA - (ahora - last_capture)):.1f}s", 
                   (10, 60), FUENTE, 0.5, COLOR_VERDE, 1)
        
        if estado:
            color = COLOR_VERDE if estado == "PERMITIDO" else COLOR_ROJO
            cv2.putText(frame, f"ESTADO: {estado}", (10, 90), FUENTE, 0.8, color, 2)

        cv2.imshow('Sistema LPR - UNEFA 2026', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("✅ Finalizado")

if __name__ == "__main__":
    main()