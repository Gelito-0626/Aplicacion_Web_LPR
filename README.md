# 🛡️ AEGIS LPR - Control Perimetral Autónomo

Sistema de Reconocimiento de Matrículas (License Plate Recognition) para control de acceso vehicular en entornos militares.

## 📸 Modos de Operación

| Modo | Entrada | Tecnología |
|------|---------|------------|
| **Automático** | Imagen de placa | YOLOv8 + PyTesseract OCR |
| **Manual** | Texto ingresado por operador | Validación directa contra BD |

El módulo de cámara en vivo (`agente_lpr.py`) está disponible para entornos con hardware adecuado.

---

## 🔄 Diagramas de Flujo

### Proceso 1: Detección Automática

```mermaid
flowchart TD
    inicio1([INICIO]) --> A[Imagen de placa recibida]
    A --> B[YOLOv8 procesa imagen]
    B --> C[PyTesseract extrae caracteres]
    C --> D{Placa en base de datos?}
    
    D -->|SI| E[Verificar horario y dias]
    E --> F{Dentro del horario?}
    F -->|SI| G[ACCESO PERMITIDO]
    F -->|NO| H[ACCESO DENEGADO]
    
    D -->|NO| I[Alerta: Vehiculo desconocido]
    I --> J[Notificar guardia de turno]
    J --> H
    
    G --> K[Registrar en RegistroAcceso]
    H --> K
    K --> L[WebSocket: Actualizar Dashboard]
    L --> fin1([FIN])  

```

### Proceso 2: Verificación Manual

```mermaid
flowchart TD
    inicio2([INICIO]) --> A[Operador ingresa placa manualmente]
    A --> B[Sistema verifica en base de datos]
    B --> C{Placa registrada?}
    
    C -->|SI| D[Verificar horario y dias]
    D --> E{Dentro del horario?}
    E -->|SI| F[ACCESO PERMITIDO]
    E -->|NO| G[ACCESO DENEGADO]
    
    C -->|NO| H[Registrar como vehiculo desconocido]
    H --> G
    
    F --> I[Registro historico con marca de tiempo]
    G --> I
    I --> J[Dashboard actualizado]
    J --> fin2([FIN])

```

## 📊 Diagrama Entidad-Relación

```mermaid
erDiagram
    USUARIO {
        string carnet_militar PK
        string nombre_apellido
        string correo_electronico
        string rango
        string contrasena
    }

    VEHICULO {
        string placa PK
        string propietario
        string marca_modelo
        string color
        string tipo_vehiculo
        string estado_acceso
        string observacion
        time hora_inicio
        time hora_fin
        string dias_permitidos
    }

    REGISTRO_ACCESO {
        int id_registro PK
        string placa_leida
        datetime fecha_hora
        string estado_acceso
        string motivo_denegacion
    }

    VEHICULO ||--o{ REGISTRO_ACCESO : "genera"

```

## 🔁 Diagrama de Secuencia

```mermaid
sequenceDiagram
    participant Img as Imagen/Texto
    participant IA as YOLOv8 + PyTesseract
    participant API as Backend FastAPI
    participant DB as SQLite
    participant WS as WebSocket
    participant Dash as Dashboard

    Img->>IA: Imagen o texto de placa
    IA->>IA: Procesa y extrae caracteres
    
    alt Placa detectada correctamente
        IA->>API: POST /api/lpr/procesar-imagen
        API->>DB: SELECT placa FROM vehiculos
        DB-->>API: Datos del vehiculo
        
        alt Vehiculo autorizado y en horario
            API->>WS: Broadcast: PERMITIDO
            WS-->>Dash: Actualizar dashboard en verde
            API->>DB: INSERT INTO registro_acceso
        else Vehiculo no autorizado o fuera de horario
            API->>WS: Broadcast: DENEGADO
            WS-->>Dash: Actualizar dashboard en rojo
            API->>DB: INSERT INTO registro_acceso (motivo)
        end
        
    else Placa no detectada o ilegible
        API->>WS: Broadcast: ERROR LECTURA
        WS-->>Dash: Alerta: Placa ilegible
        API->>DB: INSERT INTO registro_acceso (error)
    end

```

## 🏗️ Diagrama de Arquitectura

```mermaid
graph TB
    subgraph Capa_Presentacion["Capa de Presentacion"]
        A[Dashboard HTML/CSS/JS]
        B[Login]
    end
    
    subgraph Capa_Negocio["Capa de Negocio - FastAPI"]
        C[WebSocket Server]
        D[REST API]
        E[SQLAlchemy ORM]
        F[Auth Controller]
        G[Vehiculo Controller]
        H[Usuario Controller]
        I[Acceso Controller]
    end
    
    subgraph Capa_Datos["Capa de Datos"]
        J[(SQLite)]
    end
    
    subgraph Capa_IA["Capa de Inteligencia Artificial"]
        K[YOLOv8 + PyTesseract]
        L[Imagen / Texto]
    end

    L -->|POST| D
    A <-->|WebSocket| C
    A -->|HTTP| D
    B -->|POST| F
    
    D --> I
    F --> E
    G --> E
    H --> E
    I --> E
    E --> J
    
    C -->|Broadcast| A

    style Capa_Presentacion fill:#1e293b,stroke:#3b82f6,color:#fff
    style Capa_Negocio fill:#1e293b,stroke:#10b981,color:#fff
    style Capa_Datos fill:#1e293b,stroke:#f59e0b,color:#fff
    style Capa_IA fill:#1e293b,stroke:#ef4444,color:#fff
    
```

## 👥 Diagrama de Casos de Uso

```mermaid
graph TD
    Guardia[Guardia de Turno]
    Admin[Administrador]
    
    subgraph Sistema["SISTEMA LPR"]
        UC1[Iniciar Sesion]
        UC2[Cambiar Contrasena]
        UC3[Ver Dashboard]
        UC4[Registrar Vehiculo]
        UC5[Editar Vehiculo]
        UC6[Eliminar Vehiculo]
        UC7[Registrar Usuario]
        UC8[Editar Usuario]
        UC9[Eliminar Usuario]
        UC10[Consultar Historial]
        UC11[Exportar CSV]
    end

    Guardia --> UC1
    Guardia --> UC3
    Guardia --> UC4
    Guardia --> UC10
    Guardia --> UC2

    Admin --> UC1
    Admin --> UC3
    Admin --> UC4
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
    Admin --> UC8
    Admin --> UC9
    Admin --> UC10
    Admin --> UC2

    UC3 -.->|include| UC1
    UC10 -.->|include| UC1
    UC5 -.->|extend| UC4
    UC6 -.->|extend| UC4
    UC8 -.->|extend| UC7
    UC9 -.->|extend| UC7
    UC11 -.->|extend| UC10

```

## 📚 Documentacion Tecnica

El proyecto utiliza **Docstrings de Python** para documentación interna. Para generar la documentación técnica automáticamente:

```bash

# Generar documentación en consola
python -m pydoc backend_lpr.controllers.acceso_controller

# Generar documentación HTML
python -m pydoc -w backend_lpr.controllers.acceso_controller
python -m pydoc -w backend_lpr.controllers.vehiculo_controller
python -m pydoc -w backend_lpr.controllers.auth_controller
python -m pydoc -w backend_lpr.controllers.usuario_controller
