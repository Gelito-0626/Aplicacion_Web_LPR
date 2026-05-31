# Guía de Contribución - Sistema LPR UNEFA

## Estructura de Ramas

Usamos Git Flow adaptado:

| Tipo de Rama | Formato | Ejemplo |
|-------------|---------|---------|
| Nueva función | `feature/<nombre>` | `feature/deteccion-placas` |
| Corrección | `fix/<nombre>` | `fix/error-cors` |
| Documentación | `docs/<nombre>` | `docs/readme` |

## Conventional Commits

Todos los commits siguen el estándar Conventional Commits:

| Tipo | Uso |
|------|-----|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de error |
| `docs` | Documentación |
| `style` | Formato de código |
| `refactor` | Reestructuración |
| `test` | Pruebas |
| `chore` | Mantenimiento |

### Ejemplos:

feat: Agregar endpoint de detección LPR
fix: Corregir error de CORS en WebSocket
docs: Actualizar diagrama de arquitectura

## Reglas de Protección

-  Prohibido hacer git push directo a main
-  Todo cambio requiere Pull Request
-  Se necesita 1 aprobación mínima
-  El pipeline de CI/CD debe pasar (verde) antes del merge

## Flujo de Trabajo

1. Crear rama desde main: `git checkout -b feature/mi-cambio`
2. Hacer cambios y commit: `git commit -m "feat: descripción"`
3. Subir rama: `git push origin feature/mi-cambio`
4. Abrir Pull Request en GitHub
5. Esperar revisión y CI/CD verde
6. Merge a main
