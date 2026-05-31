document.getElementById("auth-formulario").addEventListener("submit", async function(event) {
    event.preventDefault();

    // Leer valores de los campos
    const correo = document.getElementById("correo").value;
    const contrasena = document.getElementById("contrasena").value;

    // Validaciones rápidas en frontend (opcional)
    if (!correo || !contrasena) {
        alert("Por favor, completa todos los campos.");
        return;
    }

    // Enviar datos al backend FastAPI
    try {
        const resp = await fetch("http://127.0.0.1:8000/api/usuarios/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ correo_electronico: correo, contrasena: contrasena })
        });
        const data = await resp.json();

        if (resp.ok && data.acceso) {
            // Login exitoso, redirige al dashboard
            alert("¡Login exitoso! Redirigiendo...");
            window.location.href = "dashboard.html";
        } else {
            alert(data.motivo || "Credenciales incorrectas o usuario no autorizado.");
        }
    } catch (error) {
        alert("Error de conexión con el servidor. Inténtalo más tarde.");
        console.error(error);
    }
});