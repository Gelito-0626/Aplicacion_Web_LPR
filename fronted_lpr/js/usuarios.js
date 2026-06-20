// Gestión de Usuarios - Sistema LPR

const rango = localStorage.getItem("operador_rango");
const rangosPermitidos = ["Cnel", "Tte Coronel", "Mayor", "Cap"];
let editandoCarnet = null;

document.addEventListener("DOMContentLoaded", () => {
    if (rangosPermitidos.includes(rango)) {
        document.getElementById("btn-nuevo-usuario").style.display = "inline-flex";
    } else {
        document.getElementById("btn-nuevo-usuario").style.display = "none";
    }

    cargarUsuarios();

    document.getElementById("form-usuario").addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const carnet = document.getElementById("usr-carnet").value.trim();
        const nombre = document.getElementById("usr-nombre").value.trim();
        const correo = document.getElementById("usr-correo").value.trim();
        const rangoUsr = document.getElementById("usr-rango").value;
        
        const data = {
            carnet_militar: carnet,
            nombre_apellido: nombre,
            correo_electronico: correo,
            rango: rangoUsr,
            contrasena: "unefa123"
        };

        try {
            let url, method;
            if (editandoCarnet) {
                url = `http://127.0.0.1:8000/api/usuarios/actualizar/${editandoCarnet}`;
                method = "PUT";
            } else {
                url = "http://127.0.0.1:8000/api/usuarios/registro";
                method = "POST";
            }

            const respuesta = await fetch(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });

            const resultado = await respuesta.json();

            if (respuesta.ok || resultado.registro) {
                alert(editandoCarnet ? "✅ Usuario actualizado" : "✅ Usuario registrado. Contraseña temporal: unefa123");
                cancelarEdicion();
                cargarUsuarios();
            } else {
                alert("⚠️ " + (resultado.detail || resultado.motivo || "Error"));
            }
        } catch (error) {
            alert("❌ Error de comunicación con el servidor");
        }
    });
});

function mostrarFormulario() {
    document.getElementById("seccion-form-usuario").style.display = "block";
    document.getElementById("titulo-form-usuario").textContent = "Registrar Nuevo Usuario";
    document.getElementById("form-usuario").reset();
    document.getElementById("usr-carnet").disabled = false;
    editandoCarnet = null;
    document.getElementById("btn-guardar-usuario").innerHTML = '<i data-lucide="save"></i> Guardar Usuario';
    lucide.createIcons();
}

function cancelarEdicion() {
    document.getElementById("seccion-form-usuario").style.display = "none";
    editandoCarnet = null;
}

async function cargarUsuarios() {
    try {
        const respuesta = await fetch("http://127.0.0.1:8000/api/usuarios/listar");
        const datos = await respuesta.json();
        
        const tbody = document.getElementById("usr-tabla-body");
        tbody.innerHTML = "";
        
        if (!datos.usuarios || datos.usuarios.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px;">No hay usuarios registrados</td></tr>';
            return;
        }
        
        datos.usuarios.forEach(u => {
            const fila = document.createElement("tr");
            fila.className = "veh-fila-interactiva";
            
            let acciones = "";
            if (rangosPermitidos.includes(rango)) {
                acciones = `
                    <div class="veh-tabla-acciones">
                        <button class="veh-btn-accion veh-accion-editar" onclick="editarUsuario('${u.carnet_militar}')" title="Editar">
                            <i data-lucide="edit-2"></i>
                        </button>
                        <button class="veh-btn-accion veh-accion-eliminar" onclick="eliminarUsuario('${u.carnet_militar}')" title="Eliminar">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>`;
            } else {
                acciones = '<span style="color:#64748b; font-size:11px;">Sin permisos</span>';
            }
            
            fila.innerHTML = `
                <td><span class="veh-badge-placa">${u.carnet_militar}</span></td>
                <td>${u.nombre_apellido}</td>
                <td>${u.rango || "-"}</td>
                <td>${u.correo_electronico}</td>
                <td>${acciones}</td>
            `;
            tbody.appendChild(fila);
        });
        
        lucide.createIcons();
    } catch (error) {
        document.getElementById("usr-tabla-body").innerHTML = '<tr><td colspan="5" style="text-align:center; padding:20px; color:#ef4444;">Error al cargar</td></tr>';
    }
}

async function editarUsuario(carnet) {
    try {
        const respuesta = await fetch(`http://127.0.0.1:8000/api/usuarios/buscar/${carnet}`);
        const u = await respuesta.json();
        
        document.getElementById("usr-carnet").value = u.carnet_militar;
        document.getElementById("usr-carnet").disabled = true;
        document.getElementById("usr-nombre").value = u.nombre_apellido;
        document.getElementById("usr-correo").value = u.correo_electronico;
        document.getElementById("usr-rango").value = u.rango || "";
        
        document.getElementById("seccion-form-usuario").style.display = "block";
        document.getElementById("titulo-form-usuario").textContent = "Editar Usuario";
        document.getElementById("btn-guardar-usuario").innerHTML = '<i data-lucide="save"></i> Actualizar';
        editandoCarnet = carnet;
        lucide.createIcons();
    } catch (error) {
        alert("❌ Error al cargar datos del usuario");
    }
}

async function eliminarUsuario(carnet) {
    if (!confirm(`¿Está seguro de eliminar al usuario ${carnet}?`)) return;
    
    try {
        const respuesta = await fetch(`http://127.0.0.1:8000/api/usuarios/eliminar/${carnet}`, { method: "DELETE" });
        if (respuesta.ok) {
            alert("✅ Usuario eliminado");
            cargarUsuarios();
        }
    } catch (error) {
        alert("❌ Error al eliminar");
    }
}