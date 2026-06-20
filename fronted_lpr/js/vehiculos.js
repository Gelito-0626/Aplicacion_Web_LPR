document.addEventListener("DOMContentLoaded", () => {
    const checkAccesoLibre = document.getElementById("veh-acceso-libre");
    const contenedorReglas = document.getElementById("veh-contenedor-reglas");
    const formulario = document.getElementById("veh-formulario");
    const btnLimpiar = document.getElementById("veh-btn-limpiar");
    const busqueda = document.getElementById("veh-buscar");

    let editandoPlaca = null; // Para saber si estamos editando

    checkAccesoLibre.addEventListener("change", () => {
        contenedorReglas.style.display = checkAccesoLibre.checked ? "none" : "block";
    });

    btnLimpiar.addEventListener("click", () => {
        setTimeout(() => {
            contenedorReglas.style.display = "none";
            editandoPlaca = null;
            document.querySelector(".veh-btn-guardar").innerHTML = '<i data-lucide="save"></i> Guardar Vehículo';
        }, 10);
    });

    cargarVehiculos();

    if (busqueda) {
        busqueda.addEventListener("input", () => cargarVehiculos(busqueda.value));
    }

    formulario.addEventListener("submit", async (event) => {
        event.preventDefault();

        const placa = document.getElementById("veh-placa").value.trim().toUpperCase();
        const propietario = document.getElementById("veh-propietario").value.trim();
        const modelo = document.getElementById("veh-modelo")?.value?.trim() || "";
        const color = document.getElementById("veh-color")?.value?.trim() || "";
        const tipoVehiculo = document.getElementById("veh-tipo")?.value || "Particular";
        const estadoAcceso = document.getElementById("veh-estado")?.value || "PERMITIDO";
        const observacion = document.getElementById("veh-observacion")?.value?.trim() || "";

        let horaInicio = "00:00";
        let horaFin = "23:59";
        let diasPermitidos = "Lunes,Martes,Miercoles,Jueves,Viernes,Sabado,Domingo";

        if (!checkAccesoLibre.checked) {
            horaInicio = document.getElementById("veh-hora-inicio").value;
            horaFin = document.getElementById("veh-hora-fin").value;
            diasPermitidos = document.getElementById("veh-dias").value.trim();
            
            if (!horaInicio || !horaFin || !diasPermitidos) {
                alert("Complete los campos de horarios y dias permitidos.");
                return;
            }
        }

        const vehiculoData = {
            placa: placa,
            propietario: propietario,
            marca_modelo: modelo || "No especificado",
            color: color || "No especificado",
            tipo_vehiculo: tipoVehiculo,
            estado_acceso: estadoAcceso,
            observacion: observacion,
            hora_inicio: horaInicio,
            hora_fin: horaFin,
            dias_permitidos: diasPermitidos
        };

        try {
            let url, method;
            
            if (editandoPlaca) {
                url = `http://127.0.0.1:8000/api/vehiculos/actualizar/${editandoPlaca}`;
                method = "PUT";
            } else {
                url = "http://127.0.0.1:8000/api/vehiculos/registro";
                method = "POST";
            }

            const respuesta = await fetch(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(vehiculoData)
            });

            const resultado = await respuesta.json();

            if (respuesta.ok) {
                alert(editandoPlaca ? "✅ Vehiculo actualizado exitosamente" : "✅ Vehiculo registrado exitosamente");
                formulario.reset();
                contenedorReglas.style.display = "none";
                editandoPlaca = null;
                document.querySelector(".veh-btn-guardar").innerHTML = '<i data-lucide="save"></i> Guardar Vehículo';
                document.getElementById("veh-placa").disabled = false;
                cargarVehiculos();
            } else {
                const msg = typeof resultado.detail === "string" ? resultado.detail : JSON.stringify(resultado.detail);
                alert("⚠️ " + msg);
            }

        } catch (error) {
            console.error("Error:", error);
            alert("❌ Error de comunicacion con el servidor.");
        }
    });
});

// Cargar lista de vehiculos
async function cargarVehiculos(filtro = "") {
    try {
        let url = "http://127.0.0.1:8000/api/vehiculos/listar";
        if (filtro) url += "?busqueda=" + encodeURIComponent(filtro);
        
        const respuesta = await fetch(url);
        const datos = await respuesta.json();
        
        const tbody = document.getElementById("veh-tabla-body");
        if (!tbody) return;
        
        tbody.innerHTML = "";
        
        if (!datos.vehiculos || datos.vehiculos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:20px;">No hay vehiculos registrados</td></tr>';
            return;
        }
        
        datos.vehiculos.forEach(v => {
            const estadoClase = v.estado_acceso === "PERMITIDO" ? "veh-status-autorizado" : "veh-status-bloqueado";
            const fila = document.createElement("tr");
            fila.className = "veh-fila-interactiva";
            fila.innerHTML = `
                <td><span class="veh-badge-placa">${v.placa}</span></td>
                <td>${v.propietario || "-"}</td>
                <td>${v.marca_modelo || "-"}</td>
                <td>${v.color || "-"}</td>
                <td>${v.tipo_vehiculo || "-"}</td>
                <td><span class="veh-badge-status ${estadoClase}">${v.estado_acceso}</span></td>
                <td>
                    <div class="veh-tabla-acciones">
                        <button class="veh-btn-accion veh-accion-editar" title="Editar" onclick="editarVehiculo('${v.placa}')">
                            <i data-lucide="edit-2"></i>
                        </button>
                        <button class="veh-btn-accion veh-accion-eliminar" title="Eliminar" onclick="eliminarVehiculo('${v.placa}')">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(fila);
        });
        
        lucide.createIcons();
        
    } catch (error) {
        console.error("Error cargando vehiculos:", error);
    }
}

// Editar vehiculo
async function editarVehiculo(placa) {
    try {
        const respuesta = await fetch(`http://127.0.0.1:8000/api/vehiculos/buscar/${placa}`);
        const v = await respuesta.json();
        
        document.getElementById("veh-placa").value = v.placa;
        document.getElementById("veh-placa").disabled = true;
        document.getElementById("veh-propietario").value = v.propietario || "";
        document.getElementById("veh-modelo").value = v.marca_modelo || "";
        document.getElementById("veh-color").value = v.color || "";
        document.getElementById("veh-tipo").value = v.tipo_vehiculo || "Particular";
        document.getElementById("veh-estado").value = v.estado_acceso || "PERMITIDO";
        document.getElementById("veh-observacion").value = v.observacion || "";
        
        editandoPlaca = placa;
        document.querySelector(".veh-btn-guardar").innerHTML = '<i data-lucide="save"></i> Actualizar Vehículo';
        
        window.scrollTo({ top: 0, behavior: 'smooth' });
        lucide.createIcons();
        
    } catch (error) {
        console.error("Error cargando vehiculo:", error);
        alert("❌ Error al cargar datos del vehiculo");
    }
}

// Eliminar vehiculo
async function eliminarVehiculo(placa) {
    if (!confirm(`¿Está seguro de eliminar el vehículo con placa ${placa}?`)) return;
    
    try {
        const respuesta = await fetch(`http://127.0.0.1:8000/api/vehiculos/eliminar/${placa}`, {
            method: "DELETE"
        });
        
        if (respuesta.ok) {
            alert("✅ Vehículo eliminado exitosamente");
            cargarVehiculos();
        } else {
            const resultado = await respuesta.json();
            alert("⚠️ " + (resultado.detail || "Error al eliminar"));
        }
        
    } catch (error) {
        console.error("Error eliminando:", error);
        alert("❌ Error de comunicacion con el servidor.");
    }
}