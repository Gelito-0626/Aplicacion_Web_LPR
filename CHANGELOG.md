# Bitácora de Cambios

## [v2.0.0] - 2026-06-20

### Añadido
- Módulo de verificación por imagen con YOLO + PyTesseract
- Modo manual de ingreso de placas
- Panel deslizable de perfil con cambio de contraseña
- Modo oscuro persistente en todos los módulos
- Historial de accesos con filtros y exportación CSV
- Pruebas unitarias integradas al CI/CD (6 pruebas)
- Documentación con Docstrings en todas las funciones
- Manejo de errores con logs [ERROR] y timestamp

### Modificado
- Migración de Node.js/Express a Python 3.12 + FastAPI
- Separación de tabla Usuario (guardias) y Vehículo (dueños)
- Contadores persistentes en dashboard

### Eliminado
- Registro público de usuarios (ahora solo desde el sistema)
- Módulos de Reportes y Configuración (unificados)

### Corregido
- Comparación de horarios (str vs time)
- Filtro de duplicados en historial (10 segundos)
- Validación de formato de placa venezolana