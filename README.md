# Sistema LPR - Control Perimetral Autónomo

Sistema de Reconocimiento de Matrículas (License Plate Recognition) para control de acceso vehicular en zonas restringidas.

## Arquitectura del Sistema

```mermaid
graph TB
    subgraph "Frontend"
        A[Dashboard HTML/CSS/JS]
    end
    
    subgraph "Backend FastAPI"
        B[WebSocket Server]
        C[REST API]
        D[SQLAlchemy ORM]
    end
    
    subgraph "Base de Datos"
        E[(SQLite)]
    end
    
    subgraph "Agente IA"
        F[YOLOv8]
        G[Cámara Web]
    end
    
    G -->|Video| F
    F -->|Detección| C
    C --> D
    D --> E
    C --> B
    B -->|Tiempo Real| A