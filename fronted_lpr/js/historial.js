// ===== DETECCIÓN DE ENTORNO =====
const ES_LOCAL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const BASE_URL = ES_LOCAL ? 'http://127.0.0.1:8000' : 'https://aegis-lpr.onrender.com';

// Historial de Accesos - Sistema LPR

document.addEventListener("DOMContentLoaded", () => {
    cargarHistorial();

    document.getElementById("hist-buscar").addEventListener("input", () => cargarHistorial());
    document.getElementById("hist-estado").addEventListener("change", () => cargarHistorial());
    document.getElementById("hist-desde").addEventListener("change", () => cargarHistorial());
    document.getElementById("hist-hasta").addEventListener("change", () => cargarHistorial());
});

async function cargarHistorial() {
    const desde = document.getElementById("hist-desde").value;
    const hasta = document.getElementById("hist-hasta").value;
    const estado = document.getElementById("hist-estado").value;
    const placa = document.getElementById("hist-buscar").value.trim();

    let url = `${BASE_URL}/api/lpr/historial?`;
    const params = [];
    if (desde) params.push("desde=" + desde);
    if (hasta) params.push("hasta=" + hasta + "T23:59:59");
    if (estado) params.push("estado=" + estado);
    if (placa) params.push("placa=" + placa);
    url += params.join("&");

    try {
        const respuesta = await fetch(url);
        const datos = await respuesta.json();
        
        const tbody = document.getElementById("hist-tabla-body");
        const total = document.getElementById("hist-total");
        
        tbody.innerHTML = "";
        total.textContent = datos.total || 0;
        
        if (!datos.registros || datos.registros.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:20px;">No hay registros de acceso</td></tr>';
            return;
        }
        
        datos.registros.forEach(r => {
            const estadoClase = r.estado === "PERMITIDO" ? "veh-status-autorizado" : "veh-status-bloqueado";
            const fecha = new Date(r.fecha_hora).toLocaleString('es-VE', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit', second: '2-digit'
            });
            
            const fila = document.createElement("tr");
            fila.className = "veh-fila-interactiva";
            fila.innerHTML = `
                <td><span class="veh-badge-placa">${r.placa}</span></td>
                <td>${fecha}</td>
                <td><span class="veh-badge-status ${estadoClase}">${r.estado === "PERMITIDO" ? "Autorizado" : "Denegado"}</span></td>
                <td style="font-size:11px;">${r.motivo || "-"}</td>
            `;
            tbody.appendChild(fila);
        });
        
    } catch (error) {
        console.error("Error cargando historial:", error);
        document.getElementById("hist-tabla-body").innerHTML = '<tr><td colspan="4" style="text-align:center; padding:20px; color:red;">Error al conectar con el servidor</td></tr>';
    }
}

function exportarCSV() {
    const filas = document.querySelectorAll("#hist-tabla-body tr");
    let csv = "Placa,Fecha,Estado,Motivo\n";
    
    filas.forEach(fila => {
        const celdas = fila.querySelectorAll("td");
        if (celdas.length >= 4) {
            csv += `"${celdas[0].textContent.trim()}","${celdas[1].textContent.trim()}","${celdas[2].textContent.trim()}","${celdas[3].textContent.trim()}"\n`;
        }
    });
    
    if (filas.length === 0 || filas[0].textContent.includes("No hay registros")) {
        alert("No hay datos para exportar.");
        return;
    }
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'historial_accesos_' + new Date().toISOString().slice(0,10) + '.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}