from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import time, datetime
import re

# ==========================================
# 1. ESQUEMAS PARA AUTENTICACIÓN Y USUARIOS
# ==========================================

class UsuarioLogin(BaseModel):
    """Esquema de entrada para validar el inicio de sesión."""
    correo_electronico: EmailStr = Field(..., description="Correo electrónico institucional o civil")
    contrasena: str = Field(..., min_length=4, description="Contraseña del usuario")


class UsuarioCreate(BaseModel):
    """Esquema para validar el registro de nuevo personal militar o civil."""
    carnet_militar: str = Field(..., min_length=5, description="Carnet militar o cédula (mínimo 5 caracteres)")
    nombre_apellido: str = Field(..., min_length=3, description="Nombre y apellido completos")
    correo_electronico: EmailStr = Field(..., description="Correo electrónico válido")
    rango: Optional[str] = Field('Civil', description="Rango o jerarquía militar. Por defecto 'Civil'")
    contrasena: str = Field(..., min_length=6, description="Contraseña mínima de 6 caracteres")


# ==========================================
# 2. ESQUEMAS PARA VEHÍCULOS E IA (LPR)
# ==========================================

class DeteccionPlacaInput(BaseModel):
    """
    Esquema para recibir detecciones desde el agente LPR (IA).
    Se comunica con el endpoint POST /api/lpr/deteccion
    """
    placa: str = Field(
        ...,
        min_length=4,
        max_length=15,
        description="Placa detectada por la IA (formato bolivariano: ABCD123 o similar)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Fecha y hora exacta de la detección"
    )
    confianza: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Nivel de confianza de la detección (0.0 a 1.0)"
    )
    origen: Optional[str] = Field(
        'camara_principal',
        description="Origen de la detección (cámara, manual, etc.)"
    )
    
    @validator('placa')
    def normalizar_placa(cls, v):
        """Convierte la placa a mayúsculas, elimina espacios y valida formato"""
        if not v or not v.strip():
            raise ValueError('La placa no puede estar vacía')
        
        # Eliminar espacios y convertir a mayúsculas
        placa_limpia = v.strip().upper()
        # Eliminar caracteres no permitidos (solo letras, números y guiones)
        placa_limpia = re.sub(r'[^A-Z0-9\-]', '', placa_limpia)
        
        if len(placa_limpia) < 4:
            raise ValueError(f'Placa inválida después de limpiar: {placa_limpia}')
        
        return placa_limpia


class VehiculoCreate(BaseModel):
    """
    Esquema para el registro y parametrización de nuevos vehículos.
    Se usa en el endpoint POST /api/vehiculos/registro
    """
    placa: str = Field(
        ...,
        min_length=4,
        max_length=15,
        description="Placa vehicular en formato bolivariano (ABCD123)"
    )
    propietario: str = Field(
        ...,
        min_length=3,
        description="Carnet militar o nombre del propietario"
    )
    marca_modelo: Optional[str] = Field(
        None,
        max_length=100,
        description="Marca y modelo del vehículo (ej: Toyota Corolla)"
    )
    color: Optional[str] = Field(
        None,
        max_length=50,
        description="Color del vehículo"
    )
    tipo_vehiculo: Optional[str] = Field(
        'Particular',
        max_length=50,
        description="Tipo de vehículo (Particular, Oficial, Militar, etc.)"
    )
    estado_acceso: Optional[str] = Field(
        'PERMITIDO',
        description="Estado de acceso: PERMITIDO, DENEGADO, BLOQUEADO o INACTIVO"
    )
    observacion: Optional[str] = Field(
        None,
        max_length=500,
        description="Notas especiales de autorización o restricciones"
    )
    hora_inicio: Optional[str] = Field(
        '00:00',
        description="Hora de inicio de acceso permitido (formato HH:MM)"
    )
    hora_fin: Optional[str] = Field(
        '23:59',
        description="Hora de fin de acceso permitido (formato HH:MM)"
    )
    dias_permitidos: Optional[str] = Field(
        'Lunes,Martes,Miércoles,Jueves,Viernes,Sábado,Domingo',
        description="Días autorizados separados por comas"
    )
    
    @validator('placa')
    def validar_y_normalizar_placa(cls, v):
        """Valida y normaliza el formato de la placa"""
        if not v or not v.strip():
            raise ValueError('La placa es obligatoria')
        
        placa_limpia = v.strip().upper()
        
        # Verificar formato bolivariano (4 letras + 3 números)
        if re.match(r'^[A-Z]{4}\d{3}$', placa_limpia):
            return placa_limpia
        
        # Permitir otros formatos (letras, números y guiones)
        if re.match(r'^[A-Z0-9\-]+$', placa_limpia) and len(placa_limpia) >= 4:
            return placa_limpia
        
        raise ValueError(
            f'Formato de placa inválido: {v}. '
            'Use formato bolivariano (ABCD123) o similar'
        )
    
    @validator('estado_acceso')
    def validar_estado_acceso(cls, v):
        """Valida que el estado de acceso sea uno de los permitidos"""
        if v:
            estados_validos = ['PERMITIDO', 'DENEGADO', 'BLOQUEADO', 'INACTIVO']
            if v.upper() not in estados_validos:
                raise ValueError(
                    f'Estado de acceso inválido: {v}. '
                    f'Use: {", ".join(estados_validos)}'
                )
            return v.upper()
        return 'PERMITIDO'
    
    @validator('hora_inicio', 'hora_fin')
    def validar_formato_hora(cls, v):
        """Valida el formato de hora HH:MM"""
        if v is None:
            return v
        
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError(f'Formato de hora inválido: {v}. Use HH:MM (00:00 a 23:59)')
        return v


class VehiculoUpdate(BaseModel):
    """
    Esquema para actualizar vehículos existentes.
    Todos los campos son opcionales (solo se actualiza lo enviado).
    """
    propietario: Optional[str] = Field(None, min_length=3, description="Nombre del propietario")
    marca_modelo: Optional[str] = Field(None, max_length=100, description="Marca y modelo")
    color: Optional[str] = Field(None, max_length=50, description="Color del vehículo")
    tipo_vehiculo: Optional[str] = Field(None, max_length=50, description="Tipo de vehículo")
    estado_acceso: Optional[str] = Field(
        None,
        description="Estado: PERMITIDO, DENEGADO, BLOQUEADO o INACTIVO"
    )
    observacion: Optional[str] = Field(None, max_length=500, description="Observaciones")
    hora_inicio: Optional[str] = Field(None, description="Hora inicio (HH:MM)")
    hora_fin: Optional[str] = Field(None, description="Hora fin (HH:MM)")
    dias_permitidos: Optional[str] = Field(None, description="Días permitidos")
    
    @validator('estado_acceso')
    def validar_estado_acceso(cls, v):
        if v:
            estados_validos = ['PERMITIDO', 'DENEGADO', 'BLOQUEADO', 'INACTIVO']
            if v.upper() not in estados_validos:
                raise ValueError(f'Estado inválido: {v}. Use: {", ".join(estados_validos)}')
            return v.upper()
        return v
    
    @validator('hora_inicio', 'hora_fin')
    def validar_formato_hora(cls, v):
        if v is None:
            return v
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError(f'Formato de hora inválido: {v}. Use HH:MM')
        return v


# ==========================================
# 3. ESQUEMAS DE RESPUESTA (OUTPUTS)
# ==========================================

class RegistroAccesoResponse(BaseModel):
    """
    Esquema de salida para el historial de accesos mostrado en el Dashboard.
    """
    id_registro: int
    placa_leida: str
    fecha_hora: datetime
    estado_acceso: str
    motivo_denegacion: Optional[str] = None
    propietario: Optional[str] = None
    tipo_alerta: Optional[str] = None

    class Config:
        from_attributes = True


class VehiculoResponse(BaseModel):
    """
    Esquema de respuesta con información completa del vehículo.
    """
    id: int
    placa: str
    propietario: str
    marca_modelo: Optional[str] = None
    color: Optional[str] = None
    tipo_vehiculo: Optional[str] = None
    estado_acceso: str
    observacion: Optional[str] = None
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None
    dias_permitidos: Optional[str] = None

    class Config:
        from_attributes = True


class MensajeResponse(BaseModel):
    """
    Esquema genérico para respuestas simples del sistema.
    """
    mensaje: str
    tipo: str = "info"
    detalles: Optional[dict] = None