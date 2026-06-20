document.getElementById("auth-formulario").addEventListener("submit", async function(event) {
    event.preventDefault();

    const correo = document.getElementById("correo").value;
    const contrasena = document.getElementById("contrasena").value;

    if (!correo || !contrasena) {
        alert("Por favor, completa todos los campos.");
        return;
    }

    try {
        const resp = await fetch("http://127.0.0.1:8000/api/usuarios/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ correo_electronico: correo, contrasena: contrasena })
        });
        const data = await resp.json();

        if (resp.ok && data.acceso) {
            // Guardar datos del usuario logueado
            localStorage.setItem("operador_nombre", data.nombre);
            localStorage.setItem("operador_rango", data.rango);
            localStorage.setItem("operador_carnet", data.carnet_militar);
            
            alert("¡Login exitoso! Redirigiendo...");
            window.location.href = "dashboard.html";
        } else {
            alert(data.motivo || "Credenciales incorrectas o usuario no autorizado.");
        }
    } catch (error) {
        alert("Error de conexión con el servidor.");
        console.error(error);
    }
});