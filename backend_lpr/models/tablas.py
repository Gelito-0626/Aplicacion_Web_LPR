from sqlalchemy import Column, String, Integer, Time, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, time
from backend_lpr.config import Base

# ------------------------------------------
# MODELO DE USUARIOS
# ------------------------------------------
class Usuario(Base):
    __tablename__ = 'usuarios'
    
    # Carnet militar: clave primaria, indexado
    carnet_militar = Column(String, primary_key=True, index=True)
    nombre_apellido = Column(String, nullable=False)
    correo_electronico = Column(String, unique=True, nullable=False)
    rango = Column(String, nullable=True)    # Jerarquía militar, puede estar vacío
    contrasena = Column(String, nullable=False)
    
    # Relación uno-a-muchos con vehículos (un usuario puede tener muchos vehículos)
    vehiculos = relationship(
        'Vehiculo',
        back_populates='propietario_rel',
        cascade="all, delete-orphan"
    )

# ------------------------------------------
# MODELO DE VEHICULOS
# ------------------------------------------
class Vehiculo(Base):
    __tablename__ = 'vehiculos'
    
    # Placa: clave primaria, indexado
    placa = Column(String, primary_key=True, index=True)
    
    # Clave foránea a Usuario.carnet_militar (identifica al propietario)
    propietario = Column(String, ForeignKey('usuarios.carnet_militar'))
    
    marca_modelo = Column(String, nullable=True)
    color = Column(String, nullable=True)
    tipo_vehiculo = Column(String, nullable=True)
    
    estado_acceso = Column(String, default='Autorizado') # 'Autorizado' o 'Bloqueado'
    observacion = Column(String, nullable=True)
    
    # Control autónomo de tiempo
    hora_inicio = Column(Time, default=time(0, 0, 0))         # Por defecto 00:00:00
    hora_fin = Column(Time, default=time(23, 59, 59))         # Por defecto 23:59:59
    dias_permitidos = Column(
        String, 
        default='Lunes,Martes,Miércoles,Jueves,Viernes,Sábado,Domingo'
    )   # Todos los días
    
    # Relación inversa a Usuario
    propietario_rel = relationship(
        'Usuario',
        back_populates='vehiculos'
    )

# ------------------------------------------
# MODELO DE REGISTRO DE ACCESOS
# ------------------------------------------
class RegistroAcceso(Base):
    __tablename__ = 'registro_acceso'
    
    # ID autoincremental como clave primaria (histórico)
    id_registro = Column(Integer, primary_key=True, autoincrement=True)
    
    # Placa leída por la IA (en texto plano)
    placa_leida = Column(String, nullable=False)
    
    # Fecha y hora (por defecto, el momento de inserción)
    fecha_hora = Column(DateTime, default=datetime.now)
    
    # Estado del acceso (Permitido o Denegado)
    estado_acceso = Column(String, nullable=False)
    
    # Motivo de denegación (puede ser nulo)
    motivo_denegacion = Column(String, nullable=True)