from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import time, datetime
import re
import html

# ==========================================
# 1. ESQUEMAS PARA AUTENTICACIÓN Y USUARIOS
# ==========================================

class UsuarioLogin(BaseModel):
    """Esquema de entrada para validar el inicio de sesión."""
    correo_electronico: EmailStr = Field(..., description="Correo electrónico institucional o civil")
    contrasena: str = Field(..., min_length=4, max_length=100, description="Contraseña del usuario")
    
    @validator('contrasena')
    def sanitizar_contrasena(cls, v):
        """Sanitiza la contraseña (sin limitar caracteres especiales)"""
        return v.strip()


class UsuarioCreate(BaseModel):
    """Esquema para validar el registro de nuevo personal militar o civil."""
    carnet_militar: str = Field(..., min_length=5, max_length=20, description="Carnet militar o cédula")
    nombre_apellido: str = Field(..., min_length=3, max_length=200, description="Nombre y apellido completos")
    correo_electronico: EmailStr = Field(..., description="Correo electrónico válido")
    rango: Optional[str] = Field('Civil', max_length=50, description="Rango militar")
    contrasena: str = Field(..., min_length=6, max_length=100, description="Contraseña mínima de 6 caracteres")
    
    @validator('nombre_apellido')
    def sanitizar_nombre(cls, v):
        """Sanitiza el nombre eliminando caracteres peligrosos"""
        v = html.escape(v.strip())
        v = re.sub(r'[<>"\'%;()&+]', '', v)
        return v


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
        description="Placa detectada por la IA"
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
        max_length=50,
        description="Origen de la detección"
    )
    
    @validator('placa')
    def normalizar_placa(cls, v):
        """Convierte la placa a mayúsculas, elimina espacios y valida formato"""
        if not v or not v.strip():
            raise ValueError('La placa no puede estar vacía')
        
        placa_limpia = v.strip().upper()
        placa_limpia = re.sub(r'[^A-Z0-9\-]', '', placa_limpia)
        
        if len(placa_limpia) < 4:
            raise ValueError(f'Placa inválida después de limpiar: {placa_limpia}')
        
        # Sanitizar HTML
        placa_limpia = html.escape(placa_limpia)
        
        return placa_limpia
    
    @validator('origen')
    def validar_origen_seguro(cls, v):
        """Valida que el origen sea uno de los permitidos (previene manipulación)"""
        ORIGENES_PERMITIDOS = ['camara_principal', 'manual', 'ia', 'api']
        if v and v not in ORIGENES_PERMITIDOS:
            raise ValueError(f'Origen no autorizado: {v}')
        return v
    
    @validator('confianza')
    def validar_confianza(cls, v):
        """Asegura que la confianza esté en rango válido"""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('La confianza debe estar entre 0.0 y 1.0')
        return v


class VehiculoCreate(BaseModel):
    """
    Esquema para el registro y parametrización de nuevos vehículos.
    """
    placa: str = Field(..., min_length=4, max_length=15, description="Placa vehicular")
    propietario: str = Field(..., min_length=3, max_length=200, description="Propietario")
    marca_modelo: Optional[str] = Field(None, max_length=100, description="Marca y modelo")
    color: Optional[str] = Field(None, max_length=50, description="Color")
    tipo_vehiculo: Optional[str] = Field('Particular', max_length=50, description="Tipo")
    estado_acceso: Optional[str] = Field('PERMITIDO', max_length=20, description="Estado")
    observacion: Optional[str] = Field(None, max_length=500, description="Notas")
    hora_inicio: Optional[str] = Field('00:00', max_length=5, description="Hora inicio")
    hora_fin: Optional[str] = Field('23:59', max_length=5, description="Hora fin")
    dias_permitidos: Optional[str] = Field(
        'Lunes,Martes,Miércoles,Jueves,Viernes,Sábado,Domingo',
        max_length=200,
        description="Días autorizados"
    )
    
    @validator('placa')
    def validar_y_normalizar_placa(cls, v):
        if not v or not v.strip():
            raise ValueError('La placa es obligatoria')
        
        placa_limpia = v.strip().upper()
        placa_limpia = html.escape(placa_limpia)
        
        if re.match(r'^[A-Z]{4}\d{3}$', placa_limpia):
            return placa_limpia
        
        if re.match(r'^[A-Z0-9\-]+$', placa_limpia) and len(placa_limpia) >= 4:
            return placa_limpia
        
        raise ValueError(f'Formato de placa inválido: {v}')
    
    @validator('estado_acceso')
    def validar_estado_acceso(cls, v):
        if v:
            estados_validos = ['PERMITIDO', 'DENEGADO', 'BLOQUEADO', 'INACTIVO']
            if v.upper() not in estados_validos:
                raise ValueError(f'Estado inválido: {v}. Use: {", ".join(estados_validos)}')
            return v.upper()
        return 'PERMITIDO'
    
    @validator('hora_inicio', 'hora_fin')
    def validar_formato_hora(cls, v):
        if v is None:
            return v
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError(f'Formato de hora inválido: {v}. Use HH:MM')
        return v
    
    @validator('propietario', 'marca_modelo', 'color', 'observacion')
    def sanitizar_campos_texto(cls, v):
        """Sanitiza campos de texto contra XSS"""
        if v:
            v = html.escape(str(v))
            v = re.sub(r'[<>"\'%;()&+]', '', v)
        return v


class VehiculoUpdate(BaseModel):
    """Esquema para actualizar vehículos existentes."""
    propietario: Optional[str] = Field(None, min_length=3, max_length=200)
    marca_modelo: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    tipo_vehiculo: Optional[str] = Field(None, max_length=50)
    estado_acceso: Optional[str] = Field(None, max_length=20)
    observacion: Optional[str] = Field(None, max_length=500)
    hora_inicio: Optional[str] = Field(None, max_length=5)
    hora_fin: Optional[str] = Field(None, max_length=5)
    dias_permitidos: Optional[str] = Field(None, max_length=200)
    
    @validator('estado_acceso')
    def validar_estado_acceso(cls, v):
        if v:
            estados_validos = ['PERMITIDO', 'DENEGADO', 'BLOQUEADO', 'INACTIVO']
            if v.upper() not in estados_validos:
                raise ValueError(f'Estado inválido: {v}')
            return v.upper()
        return v
    
    @validator('hora_inicio', 'hora_fin')
    def validar_formato_hora(cls, v):
        if v is None:
            return v
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', v):
            raise ValueError(f'Formato de hora inválido: {v}')
        return v


# ==========================================
# 3. ESQUEMAS DE RESPUESTA (OUTPUTS)
# ==========================================

class RegistroAccesoResponse(BaseModel):
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
    mensaje: str
    tipo: str = "info"
    detalles: Optional[dict] = None


# ==========================================
# 4. FUNCIONES DE SANITIZACIÓN
# ==========================================

def sanitizar_texto(texto: str) -> str:
    """
    Sanitiza texto eliminando caracteres peligrosos.
    Previene XSS e inyección de código.
    """
    if not texto:
        return texto
    
    texto = html.escape(str(texto))
    texto = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', texto)
    
    if len(texto) > 1000:
        texto = texto[:1000]
    
    return texto.strip()