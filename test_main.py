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
    """Prueba 4: Login con credenciales correctas"""
    # Asegurar que el admin existe en la BD de prueba
    client.post("/api/usuarios/registro", json={
        "carnet_militar": "00000000",
        "nombre_apellido": "Admin Test",
        "correo_electronico": "comandante@seguridad.mil.ve",
        "rango": "Cnel",
        "contrasena": "admin123"
    })
    response = client.post("/api/usuarios/login", json={
        "correo_electronico": "comandante@seguridad.mil.ve",
        "contrasena": "admin123"
    })
    data = response.json()
    assert data["acceso"] == True
    assert "nombre" in data
    assert "rango" in data


def test_listar_vehiculos():
    """Prueba 5: El endpoint de vehiculos responde con lista"""
    response = client.get("/api/vehiculos/listar")
    assert response.status_code == 200
    assert "vehiculos" in response.json()


def test_procesar_placa_manual():
    """Prueba 6: Procesar una placa manualmente"""
    response = client.post("/api/lpr/procesar-imagen", data={
        "placa_manual": "XYZ999"
    })
    assert response.status_code == 200
    data = response.json()
    assert "estado" in data
    assert "placa" in data