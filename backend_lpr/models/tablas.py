from sqlalchemy import Column, String, Integer, Time, DateTime
from datetime import datetime, time
from backend_lpr.config import Base

# ------------------------------------------
# MODELO DE USUARIOS (Solo personal de seguridad)
# ------------------------------------------
class Usuario(Base):
    __tablename__ = 'usuarios'
    
    carnet_militar = Column(String, primary_key=True, index=True)
    nombre_apellido = Column(String, nullable=False)
    correo_electronico = Column(String, unique=True, nullable=False)
    rango = Column(String, nullable=True)
    contrasena = Column(String, nullable=False)

# ------------------------------------------
# MODELO DE VEHICULOS
# ------------------------------------------
class Vehiculo(Base):
    __tablename__ = 'vehiculos'
    
    placa = Column(String, primary_key=True, index=True)
    
    # Ahora es texto libre: "Juan Perez - C.I. 12345678"
    propietario = Column(String, nullable=False)
    
    marca_modelo = Column(String, nullable=True)
    color = Column(String, nullable=True)
    tipo_vehiculo = Column(String, nullable=True)
    
    estado_acceso = Column(String, default='PERMITIDO')
    observacion = Column(String, nullable=True)
    
    hora_inicio = Column(Time, default=time(0, 0, 0))
    hora_fin = Column(Time, default=time(23, 59, 59))
    dias_permitidos = Column(
        String, 
        default='Lunes,Martes,Miércoles,Jueves,Viernes,Sábado,Domingo'
    )

# ------------------------------------------
# MODELO DE REGISTRO DE ACCESOS
# ------------------------------------------
class RegistroAcceso(Base):
    __tablename__ = 'registro_acceso'
    
    id_registro = Column(Integer, primary_key=True, autoincrement=True)
    placa_leida = Column(String, nullable=False)
    fecha_hora = Column(DateTime, default=datetime.now)
    estado_acceso = Column(String, nullable=False)
    motivo_denegacion = Column(String, nullable=True)