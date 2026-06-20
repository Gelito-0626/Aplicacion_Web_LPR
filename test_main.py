"""
Pruebas Unitarias - Sistema AEGIS LPR
Ejecutar: pytest test_main.py -v
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_servidor_online():
    """Prueba 1: El servidor responde en la ruta principal"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_health_check():
    """Prueba 2: El endpoint de salud responde correctamente"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_fallido():
    """Prueba 3: Login con credenciales incorrectas devuelve acceso falso"""
    response = client.post("/api/usuarios/login", json={
        "correo_electronico": "noexiste@test.com",
        "contrasena": "mala"
    })
    assert response.json()["acceso"] == False


def test_login_exitoso():
    """Prueba 4: Login con credenciales correctas devuelve acceso verdadero"""
    response = client.post("/api/usuarios/login", json={
        "correo_electronico": "comandante@seguridad.mil.ve",
        "contrasena": "admin123"
    })
    assert response.json()["acceso"] == True


def test_listar_vehiculos():
    """Prueba 5: El endpoint de vehiculos responde con lista"""
    response = client.get("/api/vehiculos/listar")
    assert response.status_code == 200
    assert "vehiculos" in response.json()


def test_historial_accesos():
    """Prueba 6: El historial de accesos responde correctamente"""
    response = client.get("/api/lpr/historial")
    assert response.status_code == 200
    assert "registros" in response.json()