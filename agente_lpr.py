# Agente_LPR.py - 2026
import cv2
import time
import requests
from datetime import datetime
from ultralytics import YOLO

MODELO_PATH = 'best.pt'
INTERVALO_INFERENCIA = 1.2
TIEMPO_OVERLAY = 2.0
VENTANA = 'Sistema LPR - UNEFA 2026'
BACKEND_URL = 'http://localhost:8000/api/lpr/deteccion'

COLOR_VERDE = (0, 255, 0)
COLOR_ROJO = (0, 0, 255)
COLOR_AZUL = (255, 0, 0)
GROSOR_RECT = 2
FUENTE = cv2.FONT_HERSHEY_SIMPLEX
ESCALA_FUENTE = 0.68
GROSOR_TEXTO = 2
AJUSTE_TAG = 12

ultima_placa = ""
ultimo_envio = 0

def main():
    global ultima_placa, ultimo_envio
    
    print("🔄 Cargando modelo...")
    model = YOLO(MODELO_PATH)
    print("✅ Modelo cargado")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara")
        return
    
    print("✅ Cámara lista. Presiona 'q' para salir.")
    print(f"📡 Enviando a: {BACKEND_URL}")

    last_infer = 0
    overlays = []
    estado = None

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.2)
            continue

        frame = cv2.flip(frame, 1)
        ahora = time.time()

        if ahora - last_infer >= INTERVALO_INFERENCIA:
            last_infer = ahora
            chars_boxes = []

            results = model(frame, verbose=False)[0]

            if results.boxes is not None and len(results.boxes) > 0:
                for box in results.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    label = model.names[cls_id]
                    chars_boxes.append((x1, label, (x1, y1, x2, y2), conf))
            
            if chars_boxes:
                chars_boxes.sort(key=lambda c: c[0])
                placa = ''.join([c[1] for c in chars_boxes])
                confianza = sum([c[3] for c in chars_boxes]) / len(chars_boxes)

                overlays.append((ahora + TIEMPO_OVERLAY, chars_boxes, placa))

                print(f"🎯 Detectado: {placa} ({confianza:.2f})")

                # ENVIAR AL BACKEND
                if placa != ultima_placa or (ahora - ultimo_envio) > 3:
                    try:
                        r = requests.post(BACKEND_URL, json={
                            "placa": placa,
                            "timestamp": datetime.now().isoformat(),
                            "confianza": round(confianza, 2),
                            "origen": "camara_principal"
                        }, timeout=2)
                        if r.status_code == 200:
                            res = r.json()
                            estado = res.get('estado', '?')
                            print(f"📤 Dashboard: {placa} → {estado}")
                            ultima_placa = placa
                            ultimo_envio = ahora
                        else:
                            print(f"❌ Error servidor: {r.status_code}")
                    except Exception as e:
                        print(f"❌ Sin conexion: {e}")

        # Dibujar overlays
        overlays = [ov for ov in overlays if ov[0] > ahora]
        for _, chars_boxes, _ in overlays:
            for _, _, (x1, y1, x2, y2), conf in chars_boxes:
                cv2.rectangle(frame, (x1, y1), (x2, y2), COLOR_VERDE, GROSOR_RECT)
                cv2.putText(frame, f"{conf*100:.1f}%", (x1, max(y1-12, 10)), 
                           FUENTE, 0.68, COLOR_VERDE, GROSOR_TEXTO, cv2.LINE_AA)

        # Mostrar estado
        if estado:
            color = COLOR_VERDE if estado == "PERMITIDO" else COLOR_ROJO
            cv2.putText(frame, f"ESTADO: {estado}", (10, 30), FUENTE, 0.8, color, 2)

        cv2.imshow(VENTANA, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("✅ Finalizado")

if __name__ == "__main__":
    main()