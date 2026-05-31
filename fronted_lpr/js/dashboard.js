let ws;

function conectar() {
    ws = new WebSocket('ws://127.0.0.1:8000/ws/monitoreo');

    ws.onopen = function() {
        console.log("🟢 Conectado al servidor perimetral");
    };

    ws.onclose = function() {
        console.log("🔴 Reconectando en 3s...");
        setTimeout(conectar, 3000);
    };

    ws.onmessage = function(event) {
        const msg = JSON.parse(event.data);
        
        if (msg.tipo === 'conexion') return;
        
        const data = (msg.tipo === 'alerta' && msg.datos) ? msg.datos : msg;
        
        const placa = data.placa || "---";
        const propietario = data.propietario || "Desconocido";
        const motivo = data.mensaje || "";
        const estado = data.estado === "PERMITIDO" ? "Permitido" : "Denegado";
        const fechaHora = data.timestamp || new Date().toISOString();

        // 🛡️ CONTROL DE SEGURIDAD: Evita que el script muera si no encuentra el nodo de la placa
        const placaSpan = document.querySelector('.dash-matricula-letras');
        if (placaSpan) {
            placaSpan.textContent = placa;
        }
        
        // Actualizar ficha lateral de detalles
        const filas = document.querySelectorAll('.dash-ficha-valor');
        if (filas.length >= 3) {
            filas[0].textContent = propietario;
            filas[1].textContent = estado; // Asegúrate de que esta celda sea para el estado en tu HTML
            filas[2].textContent = motivo;
        }

        // Indicador de acceso visual grande con actualización de iconos Lucide
        const indicador = document.querySelector('.dash-indicador-acceso');
        if (indicador) {
            if (estado === "Permitido") {
                indicador.className = "dash-indicador-acceso dash-acceso-autorizado";
                indicador.innerHTML = '<i data-lucide="check-circle-2"></i> ACCESO PERMITIDO';
            } else {
                indicador.className = "dash-indicador-acceso dash-acceso-denegado";
                indicador.innerHTML = '<i data-lucide="x-circle"></i> ACCESO DENEGADO';
            }
            // Re-renderizar iconos dinámicos de Lucide
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }

        // Inserción dinámica en la tabla histórica en tiempo real
        const tbody = document.querySelector('.dash-tabla tbody');
        if (tbody) {
            const clase = estado === 'Permitido' ? "dash-badge-autorizado" : "dash-badge-denegado";
            const texto = estado === 'Permitido' ? "Autorizado" : "Denegado";
            
            let hora = "--:--:--";
            try {
                hora = new Date(fechaHora).toLocaleTimeString('es-VE', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
            } catch(e) {
                console.error("Error procesando fecha:", e);
            }

            const row = document.createElement('tr');
            row.innerHTML = `
                <td><span class="dash-tabla-placa">${placa}</span></td>
                <td>${hora}</td>
                <td><span class="dash-badge-acc ${clase}">${texto}</span></td>
                <td>${motivo}</td>
            `;
            
            tbody.prepend(row);
            
            // Mantener el búfer de la tabla optimizado a un máximo de 15 filas
            while (tbody.children.length > 15) {
                tbody.removeChild(tbody.lastChild);
            }
        }
    };
}

conectar();