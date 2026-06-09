# Buenas prácticas para desarrollo de sistemas web

## 1. Principios base

- Construir simple primero.
- Separar frontend, API, base de datos y workers.
- Usar TypeScript en frontend.
- Usar validación fuerte en frontend y backend.
- No confiar en datos enviados por el cliente.
- Todo acceso a datos debe pasar por permisos.
- Automatizar pruebas, despliegue y revisiones de seguridad.
- Medir errores, rendimiento y uso real del sistema.

---

## 2. Stack recomendado

```txt
Frontend:
Next.js + React + TypeScript + Tailwind CSS + shadcn/ui

Backend:
Python 3 + FastAPI + Pydantic + SQLAlchemy + Alembic

Base de datos:
PostgreSQL

Cache / sesiones / rate limit:
Redis

Auth:
OIDC/OAuth2 con Keycloak, Auth0, Clerk o similar

Infra:
Docker + CI/CD + Cloudflare/CDN + PostgreSQL administrado

Observabilidad:
Sentry + OpenTelemetry + Prometheus + Grafana
```

---

## 3. Backend y API

Buenas prácticas:

- Crear endpoints simples y predecibles.
- Usar nombres claros: `/users`, `/projects`, `/orders`.
- Separar capas:

```txt
router → service → repository → database
```

- Validar entrada con Pydantic.
- No devolver campos sensibles.
- Usar paginación en listados.
- Usar filtros controlados, no SQL dinámico inseguro.
- Versionar API si cambia mucho:

```txt
/api/v1/users
/api/v1/projects
```

- Documentar con OpenAPI.
- Proteger endpoints internos.
- Revisar permisos en cada operación.

Riesgo principal en APIs: permitir acceso a datos ajenos manipulando IDs. Cada endpoint debe validar autorización real sobre el recurso solicitado.

Referencia: OWASP API Security Top 10 2023, Broken Object Level Authorization.  
https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/

---

## 4. Seguridad mínima obligatoria

```txt
HTTPS obligatorio
CORS restringido
Rate limiting
Cookies HttpOnly + Secure + SameSite
JWT/OIDC bien validado
Contraseñas con hashing fuerte
Permisos por rol y por recurso
Logs de auditoría
Backups automáticos
Secrets fuera del repositorio
Validación de entrada
Manejo seguro de errores
```

No hacer:

```txt
No guardar tokens largos en localStorage.
No aceptar user_id desde el frontend para acciones sensibles.
No exponer PostgreSQL a internet.
No mostrar stack traces en producción.
No subir .env al repositorio.
No usar permisos solo en frontend.
```

OWASP recomienda revisar autorización, manejo de sesión, atributos de cookies, CSRF, expiración de sesión, validación de entrada y manejo de errores.

Referencia: OWASP Web Security Testing Guide.  
https://owasp.org/www-project-web-security-testing-guide/

---

## 5. Base de datos

Usar PostgreSQL como primera opción.

Buenas prácticas:

```txt
Migraciones con Alembic
Índices en campos de búsqueda
Backups con restauración probada
Usuarios DB con mínimos privilegios
Conexiones mediante pool
No exponer la DB públicamente
Auditoría en tablas sensibles
Soft delete si hay datos críticos
Timestamps: created_at, updated_at
UUID o IDs no predecibles en recursos sensibles
```

Tablas base recomendadas:

```txt
id
created_at
updated_at
created_by
updated_by
deleted_at
status
```

---

## 6. Calidad de código

Reglas simples:

```txt
Funciones cortas
Nombres claros
Una responsabilidad por archivo
Sin lógica de negocio en componentes UI
Sin queries SQL mezcladas en routers
Tests para permisos y errores
Lint obligatorio
Formateo automático
Revisión de código antes de producción
```

Herramientas:

```txt
Frontend:
ESLint
Prettier
Vitest
Playwright

Backend:
Ruff
Pytest
Mypy o Pyright

Seguridad:
Semgrep
Trivy
Gitleaks
pip-audit
npm audit
```

---

## 7. CI/CD

Pipeline mínimo:

```txt
Instalar dependencias
Revisar formato
Ejecutar lint
Ejecutar tests
Revisar tipos
Escanear secretos
Escanear vulnerabilidades
Construir Docker image
Desplegar a staging
Aprobar producción manualmente
```

Regla: no desplegar directo a producción sin pasar pruebas.

---

# 8. Diseño de interfaz de usuario

## Objetivo

La interfaz debe poder usarse sin manual.

Eso se logra con:

```txt
Claridad
Consistencia
Jerarquía visual
Textos simples
Acciones visibles
Estados claros
Errores entendibles
Flujos cortos
```

---

## 9. Principios UX básicos

### Navegación

- Menú principal visible.
- Máximo 5 a 7 opciones principales.
- Usar nombres simples:

```txt
Inicio
Clientes
Proyectos
Reportes
Configuración
Ayuda
```

- Mostrar siempre dónde está el usuario.
- Usar breadcrumbs en sistemas grandes:

```txt
Inicio > Clientes > Cliente A > Facturas
```

---

### Botones

Usar tres niveles:

```txt
Primario: acción principal
Secundario: acción alternativa
Terciario: acción menor
```

Ejemplo:

```txt
Guardar
Cancelar
Eliminar
```

Reglas:

- Un botón principal por pantalla.
- No usar muchos colores para botones.
- Botones destructivos siempre en rojo.
- Confirmar acciones irreversibles.

---

### Formularios

Buenas prácticas:

```txt
Label siempre visible
Placeholder solo como ayuda
Validación inmediata
Mensajes de error claros
Campos obligatorios marcados
Agrupar campos relacionados
No pedir datos innecesarios
Guardar progreso si el formulario es largo
```

Mal mensaje:

```txt
Error 400
```

Buen mensaje:

```txt
El correo no tiene un formato válido.
```

---

### Tablas

Para sistemas administrativos, las tablas son clave.

Deben incluir:

```txt
Búsqueda
Filtros
Ordenamiento
Paginación
Acciones por fila
Estados visibles
Exportar si aplica
```

Estados simples:

```txt
Activo
Pendiente
Bloqueado
Archivado
Eliminado
```

---

### Estados del sistema

Toda pantalla debe tener estos estados:

```txt
Cargando
Vacío
Con datos
Sin permisos
Error
Éxito
```

Ejemplo de estado vacío:

```txt
Aún no tienes clientes.
Crear primer cliente
```

---

### Feedback inmediato

Después de una acción, mostrar resultado:

```txt
Guardado correctamente.
Cambios descartados.
No tienes permisos para esta acción.
No se pudo conectar con el servidor.
```

No dejar al usuario dudando.

---

# 10. Metáforas y patrones simples

Usar patrones que la gente ya entiende:

| Necesidad | Patrón simple |
|---|---|
| Crear algo | Botón “Nuevo” o “Crear” |
| Buscar | Barra de búsqueda arriba |
| Editar | Icono lápiz + texto “Editar” |
| Eliminar | Papelera + confirmación |
| Configurar | Engranaje |
| Ver detalle | Clic en fila o botón “Ver” |
| Avanzar paso a paso | Wizard / pasos numerados |
| Filtrar datos | Panel lateral o chips |
| Acciones frecuentes | Botón visible |
| Acciones peligrosas | Zona separada y roja |
| Ayuda contextual | Texto corto junto al campo |

Evitar metáforas raras.

No inventar navegación creativa para sistemas de trabajo.

La mejor interfaz empresarial es predecible.

---

# 11. Colores recomendados

## Paleta base profesional

```txt
Primario: Azul
Secundario: Gris / Slate
Éxito: Verde
Advertencia: Amarillo / Ámbar
Error: Rojo
Información: Celeste / Azul claro
Fondo: Blanco o gris muy claro
Texto principal: Gris casi negro
Texto secundario: Gris medio
Bordes: Gris claro
```

Ejemplo práctico:

```txt
Primary: #2563EB
Primary hover: #1D4ED8

Success: #16A34A
Warning: #F59E0B
Error: #DC2626
Info: #0284C7

Background: #F8FAFC
Surface: #FFFFFF
Text: #0F172A
Muted text: #64748B
Border: #E2E8F0
```

Reglas:

- Azul para acción principal.
- Verde para éxito.
- Rojo solo para error o peligro.
- Amarillo para advertencia.
- Grises para estructura.
- No usar más de 1 color principal.
- No depender solo del color; usar texto e iconos también.

Material Design 3 organiza colores por roles de interfaz, lo que ayuda a mantener consistencia entre botones, fondos, textos y estados.

Referencia: Material Design 3 Color Roles.  
https://m3.material.io/styles/color/roles

---

# 12. Contraste y accesibilidad

Reglas mínimas:

```txt
Texto normal: contraste mínimo 4.5:1
Texto grande: contraste mínimo 3:1
Elementos de interfaz: contraste mínimo 3:1
Focus visible al navegar con teclado
No usar texto gris muy claro
No usar botones sin estado visible
```

WCAG 2.2 mantiene criterios de contraste para que el texto sea legible para personas con baja visión o menor percepción de contraste.

Referencia: WCAG 2.2.  
https://www.w3.org/TR/WCAG22/

---

# 13. Tipografías recomendadas

## Opción segura para apps web

```txt
Inter
Roboto
System UI
Segoe UI
SF Pro
Arial
```

## Recomendación directa

Usar:

```css
font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

## Tamaños recomendados

```txt
Título grande: 32px
Título de página: 24px
Subtítulo: 20px
Texto normal: 16px
Texto secundario: 14px
Label: 14px
Texto pequeño: 12px
```

## Pesos

```txt
Regular: 400
Medium: 500
Semibold: 600
Bold: 700
```

Reglas:

- No usar más de 2 tipografías.
- Para sistemas web, mejor una sola tipografía.
- Texto normal mínimo 16px.
- Evitar párrafos largos.
- Usar títulos claros.
- Mantener buena altura de línea:

```txt
line-height: 1.4 a 1.6
```

Material Design 3 usa roles tipográficos como display, headline, title, label y body para ordenar jerarquía visual y legibilidad.

Referencia: Material Design 3 Typography.  
https://m3.material.io/styles/typography/applying-type

---

# 14. Componentes UI esenciales

Todo sistema web debería tener:

```txt
Layout base
Sidebar
Topbar
Breadcrumbs
Cards
Tables
Forms
Inputs
Selects
Date picker
Modals
Toasts
Alerts
Tabs
Badges
Pagination
Search
Filters
Dropdown menu
User menu
Empty states
Loading skeletons
Error pages
Permission denied page
```

---

# 15. Reglas para que no necesite manual

```txt
Cada pantalla debe tener un título claro.
Cada acción debe usar un verbo.
Cada error debe decir cómo corregirlo.
Cada formulario debe explicar solo lo necesario.
Cada flujo debe tener máximo 3 pasos si es posible.
Cada pantalla debe tener una acción principal evidente.
Cada estado vacío debe decir qué hacer ahora.
Cada permiso bloqueado debe explicar por qué.
Cada cambio importante debe confirmar éxito o error.
```

Ejemplos de buenos textos:

```txt
Crear cliente
Guardar cambios
Enviar invitación
Descargar reporte
No tienes permisos para editar este proyecto.
Selecciona una fecha válida.
No hay resultados para esta búsqueda.
```

Evitar textos vagos:

```txt
Aceptar
Procesar
Enviar datos
Error inesperado
Operación inválida
```

---

# 16. Checklist final

Antes de lanzar:

```txt
Login seguro
Permisos probados
HTTPS activo
CORS restringido
Rate limit activo
Backups configurados
Logs funcionando
Errores monitoreados
Tests principales pasando
Formularios validados
Contraste accesible
Responsive probado
Estados vacíos creados
Mensajes de error claros
Documentación técnica mínima
CI/CD funcionando
```

---

# Regla final

Un buen sistema web debe ser:

```txt
Seguro
Rápido
Simple
Consistente
Observable
Fácil de usar
Fácil de mantener
```
