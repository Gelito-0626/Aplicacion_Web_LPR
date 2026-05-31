document.getElementById("reg-formulario").addEventListener("submit", async function(event) {
    event.preventDefault();

    // Leer valores del formulario
    const nombre = document.getElementById("reg-nombre").value;
    const correo = document.getElementById("reg-correo").value;
    const carnet = document.getElementById("reg-carnet").value;
    const rango = document.getElementById("reg-rango").value || "Civil";
    const clave = document.getElementById("reg-clave").value;
    const confirmar = document.getElementById("reg-confirmar").value;

    // Validación de contraseña igual
    if (clave !== confirmar) {
        mostrarError("Las contraseñas no coinciden.");
        return;
    }

    // Opcional: validación simple de campos vacíos...

    try {
        const resp = await fetch("http://127.0.0.1:8000/api/usuarios/registro", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                carnet_militar: carnet,
                nombre_apellido: nombre,
                correo_electronico: correo,
                rango: rango,
                contrasena: clave
            })
        });
        const data = await resp.json();

        if (data.registro) {
            alert("¡Registro exitoso! Ahora puedes iniciar sesión.");
            window.location.href = "login.html";
        } else {
            mostrarError(data.motivo || "No se pudo registrar.");
        }
    } catch (error) {
        mostrarError("Error de conexión con el servidor.");
    }
});

function mostrarError(msg) {
    const alerta = document.getElementById("reg-alerta-error");
    const texto = document.getElementById("reg-texto-error");
    texto.textContent = msg;
    alerta.classList.remove("reg-oculto");
    setTimeout(() => alerta.classList.add("reg-oculto"), 4000);
}

// Accion del botón limpiar:
document.getElementById("reg-btn-limpiar").addEventListener("click", () => {
    document.getElementById("reg-formulario").reset();
});