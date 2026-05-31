document.addEventListener("DOMContentLoaded", () => {
    const checkAccesoLibre = document.getElementById("veh-acceso-libre");
    const contenedorReglas = document.getElementById("veh-contenedor-reglas");
    const formulario = document.getElementById("veh-formulario");
    const btnLimpiar = document.getElementById("veh-btn-limpiar");

    // 1. DINÁMICA DE LA INTERFAZ: Mostrar/Ocultar horas y días al cambiar el Checkbox
    checkAccesoLibre.addEventListener("change", () => {
        if (checkAccesoLibre.checked) {
            contenedorReglas.style.display = "none"; // Si es acceso libre, se esconde
        } else {
            contenedorReglas.style.display = "block"; // Si se desmarca, aparecen las horas y días
        }
    });

    // Asegurar que el botón de limpiar también resetee la visibilidad de las reglas
    btnLimpiar.addEventListener("click", () => {
        setTimeout(() => {
            contenedorReglas.style.display = "none";
        }, 10);
    });

    // 2. CONEXIÓN CON EL BACKEND: Procesar el formulario y enviarlo a FastAPI
    formulario.addEventListener("submit", async (event) => {
        event.preventDefault(); // Evita que la página se recargue

        // Capturamos los datos básicos del formulario HTML
        const placa = document.getElementById("veh-placa").value.trim().toUpperCase();
        const propietarioCedula = document.getElementById("veh-propietario").value.trim();
        const modelo = document.getElementById("veh-modelo").value.trim();
        const color = document.getElementById("veh-color").value.trim();
        const tipoVehiculo = document.getElementById("veh-tipo").value;
        const estadoAcceso = document.getElementById("veh-estado").value;

        // Definimos los valores por defecto si el vehículo es de Acceso Libre 24/7
        let horaInicio = "00:00";
        let horaFin = "23:59";
        let diasPermitidos = "Lunes,Martes,Miercoles,Jueves,Viernes,Sabado,Domingo";

        // Si el guardia DESMARCÓ el acceso libre, agarramos las horas y días reales que escribió
        if (!checkAccesoLibre.checked) {
            horaInicio = document.getElementById("veh-hora-inicio").value;
            horaFin = document.getElementById("veh-hora-fin").value;
            diasPermitidos = document.getElementById("veh-dias").value.trim();
            
            if (!horaInicio || !horaFin || !diasPermitidos) {
                alert("Por favor, complete los campos de horarios y días permitidos.");
                return;
            }
        }

        // Armamos el objeto JSON con la estructura exacta que espera el endpoint del Backend
        const vehiculoData = {
            placa: placa,
            propietario_cedula: propietarioCedula,
            tipo_vehiculo: tipoVehiculo,
            hora_inicio: horaInicio,
            hora_fin: horaFin,
            dias_permitidos: diasPermitidos
        };

        try {
            // Hacemos la petición HTTP POST al endpoint que creamos en FastAPI
            const respuesta = await fetch("http://127.0.0.1:8000/api/vehiculos/registrar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(vehiculoData)
            });

            const resultado = await respuesta.json();

            if (respuesta.ok && resultado.guardado) {
                alert(`✅ Éxito: ${resultado.mensaje}`);
                formulario.reset(); // Limpia los campos de texto
                contenedorReglas.style.display = "none"; // Vuelve a ocultar la sección de horas
                
                // Aquí podrías llamar a una función para actualizar la tabla visual (lo haremos luego)
            } else {
                // Muestra el motivo de error devuelto por la base de datos SQLite (ej: Cédula no existe)
                alert(`⚠️ Atención: ${resultado.motivo || "No se pudo registrar el vehículo."}`);
            }

        } catch (error) {
            console.error("Error en la conexión con la API:", error);
            alert("❌ Error de comunicación con el servidor LPR. Asegúrate de que el backend esté encendido.");
        }
    });
});