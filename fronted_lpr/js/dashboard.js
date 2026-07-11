// ===== DETECCIÓN DE ENTORNO =====
const ES_LOCAL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const BASE_URL = ES_LOCAL ? 'http://127.0.0.1:8000' : 'https://aegis-lpr.onrender.com';
const WS_URL = ES_LOCAL ? 'ws://127.0.0.1:8000/ws/monitoreo' : 'wss://aegis-lpr.onrender.com/ws/monitoreo';

// ✅ Limpiar registros viejos si es un nuevo día
const hoy = new Date().toDateString();
const ultimoDia = localStorage.getItem("ultimoDiaDashboard");
if (ultimoDia !== hoy) {
    localStorage.removeItem("placasDashboard");
    localStorage.setItem("contadorAccesos", "0");
    localStorage.setItem("contadorDenegados", "0");
    localStorage.setItem("ultimoDiaDashboard", hoy);
}

// ===== SISTEMA DE ALARMA =====
let alarmaActiva = false;
let intervaloAlarma = null;
let audioContext = null;
let osciladoresActivos = [];

function iniciarAudio() {
    if (!audioContext || audioContext.state === 'closed') {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }
}
document.addEventListener('click', iniciarAudio);

function reproducirAlerta() {
    try {
        osciladoresActivos.forEach(osc => {
            try { osc.stop(); } catch(e) {}
        });
        osciladoresActivos = [];
        
        if (!audioContext || audioContext.state === 'closed') {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        const ctx = audioContext;
        
        function tono(frecuencia, inicio, duracion, volumen) {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain); 
            gain.connect(ctx.destination);
            osc.type = 'square';
            osc.frequency.setValueAtTime(frecuencia, ctx.currentTime + inicio);
            gain.gain.setValueAtTime(volumen, ctx.currentTime + inicio);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + inicio + duracion);
            osc.start(ctx.currentTime + inicio);
            osc.stop(ctx.currentTime + inicio + duracion);
            osciladoresActivos.push(osc);
        }
        
        tono(150, 0, 0.2, 0.5);
        tono(150, 0.25, 0.2, 0.5);
        tono(300, 0.5, 0.3, 0.6);
        
        setTimeout(() => {
            osciladoresActivos = [];
        }, 2000);
        
    } catch(e) {
        console.error("Error en alarma:", e);
    }
}

function activarAlarma() {
    if (alarmaActiva) return;
    alarmaActiva = true;
    reproducirAlerta();
    
    const controles = document.getElementById('alarmaControls');
    if (controles) controles.style.display = 'block';
    
    const bloque = document.getElementById('bloque-analisis');
    if (bloque) bloque.classList.add('alarma-activa');
    
    if (intervaloAlarma) clearInterval(intervaloAlarma);
    intervaloAlarma = setInterval(() => {
        if (alarmaActiva) reproducirAlerta();
    }, 2500);
}

window.silenciarAlarma = function() {
    alarmaActiva = false;
    if (intervaloAlarma) {
        clearInterval(intervaloAlarma);
        intervaloAlarma = null;
    }
    
    osciladoresActivos.forEach(osc => {
        try { osc.stop(); } catch(e) {}
    });
    osciladoresActivos = [];
    
    const controles = document.getElementById('alarmaControls');
    if (controles) controles.style.display = 'none';
    
    const indicador = document.querySelector('.dash-indicador-acceso');
    if (indicador) {
        indicador.className = "dash-indicador-acceso dash-acceso-autorizado";
        indicador.innerHTML = '<i data-lucide="check-circle-2"></i> ESPERANDO LECTURA';
    }
    
    const placaSpan = document.querySelector('.dash-matricula-letras');
    if (placaSpan) placaSpan.textContent = '---';
    
    const filas = document.querySelectorAll('.dash-ficha-valor');
    if (filas.length >= 3) { 
        filas[0].textContent = '---'; 
        filas[1].textContent = '---'; 
        filas[2].textContent = 'Esperando detección...'; 
    }
    
    const bloque = document.getElementById('bloque-analisis');
    if (bloque) bloque.classList.remove('alarma-activa');
    
    if (typeof lucide !== 'undefined') lucide.createIcons();
};

// ===== VARIABLES =====
let contadorAccesos = parseInt(localStorage.getItem("contadorAccesos") || "0");
let contadorDenegados = parseInt(localStorage.getItem("contadorDenegados") || "0");
let placasEnTabla = JSON.parse(localStorage.getItem("placasDashboard") || "[]");
let ultimaPlacaProcesada = "";
let ultimoTimestamp = 0;

function guardarPlacas() { localStorage.setItem("placasDashboard", JSON.stringify(placasEnTabla)); }
function guardarContadores() { localStorage.setItem("contadorAccesos", contadorAccesos); localStorage.setItem("contadorDenegados", contadorDenegados); }

function procesarDeteccion(data) {
    const ahora = Date.now();
    if (data.placa === ultimaPlacaProcesada && (ahora - ultimoTimestamp) < 2000) {
        console.log("⏭️ Detección duplicada, ignorando");
        return;
    }
    ultimaPlacaProcesada = data.placa;
    ultimoTimestamp = ahora;
    
    const placa = data.placa || "---";
    const propietario = data.propietario || "Desconocido";
    const estado = data.estado === "PERMITIDO" ? "Permitido" : "Denegado";
    const fechaHora = data.timestamp || new Date().toISOString();

    const placaSpan = document.querySelector('.dash-matricula-letras');
    if (placaSpan) placaSpan.textContent = placa;
    
    const filas = document.querySelectorAll('.dash-ficha-valor');
    if (filas.length >= 3) { 
        filas[0].textContent = propietario; 
        filas[1].textContent = data.detalles?.cedula || "-"; 
        filas[2].textContent = estado; 
    }
    
    const indicador = document.querySelector('.dash-indicador-acceso');
    if (indicador) {
        indicador.className = "dash-indicador-acceso " + (estado === "Permitido" ? "dash-acceso-autorizado" : "dash-acceso-denegado");
        indicador.innerHTML = estado === "Permitido" ? 
            '<i data-lucide="check-circle-2"></i> ACCESO PERMITIDO' : 
            '<i data-lucide="x-circle"></i> ACCESO DENEGADO';
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
    
    if (estado === "Denegado") {
        activarAlarma();
    }

    contadorAccesos++;
    if (estado === "Denegado") contadorDenegados++;
    guardarContadores();
    actualizarContadores();

    let fechaCompleta = "--/--/---- --:--:--";
    try {
        const d = new Date(fechaHora);
        fechaCompleta = d.toLocaleDateString('es-VE', {day:'2-digit', month:'2-digit', year:'numeric'}) + ' ' +
                        d.toLocaleTimeString('es-VE', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
    } catch(e) {}
    
    const nuevo = { placa, fecha: fechaCompleta, estado, propietario };
    placasEnTabla.unshift(nuevo); 
    if (placasEnTabla.length > 15) placasEnTabla.pop();
    guardarPlacas(); 
    agregarFilaTabla(nuevo);
}

function actualizarContadores() {
    const elAccesos = document.getElementById('dash-total-accesos');
    const elDenegados = document.getElementById('dash-total-denegados');
    if (elAccesos) elAccesos.textContent = contadorAccesos;
    if (elDenegados) elDenegados.textContent = contadorDenegados;
}

function agregarFilaTabla(r) {
    const tbody = document.getElementById('dash-tabla-body') || document.querySelector('.dash-tabla tbody');
    if (!tbody) return;
    const clase = r.estado === 'Permitido' ? "dash-badge-autorizado" : "dash-badge-denegado";
    const texto = r.estado === 'Permitido' ? "Autorizado" : "Denegado";
    const row = document.createElement('tr');
    row.innerHTML = `<td><span class="dash-tabla-placa">${r.placa}</span></td><td>${r.fecha}</td><td><span class="dash-badge-acc ${clase}">${texto}</span></td><td>${r.propietario}</td>`;
    
    if (tbody.firstChild) {
        tbody.insertBefore(row, tbody.firstChild);
    } else {
        tbody.appendChild(row);
    }
}

function restaurarTabla() {
    const tbody = document.getElementById('dash-tabla-body') || document.querySelector('.dash-tabla tbody');
    if (!tbody) return; 
    tbody.innerHTML = "";
    [...placasEnTabla].reverse().forEach(r => agregarFilaTabla(r));
}

async function cargarEstadisticas() {
    try {
        const r = await fetch(`${BASE_URL}/api/vehiculos/listar`);
        const datos = await r.json();
        const tr = document.getElementById('dash-total-registrados');
        if (tr) tr.textContent = datos.total || datos.length || 0;
    } catch(e) {}
}

// ===== WEBSOCKET =====
let ws = null;

function conectarWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) return;
    
    try {
        ws = new WebSocket(WS_URL);
        
        ws.onopen = function() {
            console.log("✅ WebSocket conectado");
        };
        
        ws.onmessage = function(event) {
            try {
                const mensaje = JSON.parse(event.data);
                if (mensaje.tipo === "nueva_deteccion") {
                    procesarDeteccion(mensaje);
                }
            } catch(e) {}
        };
        
        ws.onclose = function() {
            ws = null;
            setTimeout(conectarWebSocket, 3000);
        };
        
    } catch(e) {
        setTimeout(conectarWebSocket, 3000);
    }
}

conectarWebSocket();
setInterval(() => { if (ws && ws.readyState === WebSocket.OPEN) ws.send("ping"); }, 30000);

restaurarTabla();
actualizarContadores();
cargarEstadisticas();
setInterval(cargarEstadisticas, 30000);

console.log("✅ Dashboard listo -", ES_LOCAL ? "LOCAL" : "PRODUCCIÓN");