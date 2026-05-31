# Sistema LPR - Control Perimetral Autonomo

Sistema de Reconocimiento de Matriculas (License Plate Recognition) para control de acceso vehicular en zonas restringidas. Desarrollado para la UNEFA - 2026.

## Arquitectura del Sistema

```mermaid
graph TB
    subgraph Frontend
        A[Dashboard]
    end
    
    subgraph Backend
        B[WebSocket Server]
        C[REST API]
        D[SQLAlchemy ORM]
    end
    
    subgraph BaseDeDatos
        E[(SQLite)]
    end
    
    subgraph AgenteIA
        F[YOLOv8]
        G[Camara Web]
    end
    
    G -->|Video| F
    F -->|POST deteccion| C
    C --> D
    D --> E
    C --> B
    B -->|Tiempo Real| A
