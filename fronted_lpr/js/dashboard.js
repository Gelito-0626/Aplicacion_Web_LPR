let ws;
let contadorAccesos = parseInt(localStorage.getItem("contadorAccesos") || "0");
let contadorDenegados = parseInt(localStorage.getItem("contadorDenegados") || "0");
let placasEnTabla = JSON.parse(localStorage.getItem("placasDashboard") || "[]");
let tiempoUltimaDeteccion = 0;
let timeoutEspera = null;

function guardarPlacas() {
    localStorage.setItem("placasDashboard", JSON.stringify(placasEnTabla));
}

function guardarContadores() {
    localStorage.setItem("contadorAccesos", contadorAccesos);
    localStorage.setItem("contadorDenegados", contadorDenegados);
}

function conectar() {
    ws = new WebSocket('ws://127.0.0.1:8000/ws/monitoreo');
    ws.onopen = function() { console.log("🟢 Conectado"); restaurarTabla(); actualizarContadores(); };
    ws.onclose = function() { console.log("🔴 Reconectando..."); setTimeout(conectar, 3000); };
    ws.onmessage = function(event) {
        const msg = JSON.parse(event.data);
        if (msg.tipo === 'conexion') return;
        const data = (msg.tipo === 'alerta' && msg.datos) ? msg.datos : msg;
        procesarDeteccion(data);
    };
}

function procesarDeteccion(data) {
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
        indicador.innerHTML = estado === "Permitido" ? '<i data-lucide="check-circle-2"></i> ACCESO PERMITIDO' : '<i data-lucide="x-circle"></i> ACCESO DENEGADO';
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    contadorAccesos++;
    if (estado === "Denegado") contadorDenegados++;
    guardarContadores();
    actualizarContadores();

    if (!placasEnTabla.find(p => p.placa === placa)) {
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
    tbody.prepend(row);
}

function restaurarTabla() {
    const tbody = document.getElementById('dash-tabla-body') || document.querySelector('.dash-tabla tbody');
    if (!tbody) return;
    tbody.innerHTML = "";
    placasEnTabla.forEach(r => agregarFilaTabla(r));
}

async function cargarEstadisticas() {
    try {
        const r = await fetch('http://127.0.0.1:8000/api/vehiculos/listar');
        const datos = await r.json();
        const tr = document.getElementById('dash-total-registrados');
        if (tr) tr.textContent = datos.total || 0;
    } catch(e) {}
}

conectar();
cargarEstadisticas();