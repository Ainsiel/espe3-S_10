# Resumen Ejecutivo: Fábrica Agéntica con Arnés (ARNES/SDD)

Este documento resume la actividad práctica de desarrollo de software utilizando una **Fábrica Agéntica de Contención (ARNES)** sobre el ciclo de desarrollo del **PROYECTO CINCO** (Sistema ERP Web Pequeño). A continuación, se detalla el objetivo de la actividad, la arquitectura del sistema, el flujo de ejecución del caso práctico, las conclusiones y la explicación profunda de las diferencias entre operar una fábrica con y sin arnés.

---

## 1. Objetivo de la Actividad

El objetivo primordial de esta actividad práctica es **diseñar, implementar y operar una Fábrica Agéntica de Software (Fábrica SDD)** gobernada por un **Arnés de Contención (ARNES)** para desarrollar un Producto Mínimo Viable (MVP) funcional de extremo a extremo. 

### Objetivos Didácticos Clave:
* **Construcción mediante Fábrica:** Automatizar el flujo completo de ingeniería de software: traducción de requerimientos iniciales → estructuración del backlog y sprint backlog → planificación arquitectónica → generación de código (FastAPI / Next.js) → pruebas de integración y QA visual → trazabilidad inmutable y entrega.
* **Operación bajo Arnés:** Garantizar que los agentes no actúen con libre albedrío ("agencia libre"). Toda llamada al modelo y ejecución de herramientas está contenida en un marco riguroso de políticas, presupuestos y validadores.
* **Gobernanza y Trazabilidad:** Mantener una bitácora detallada de ejecución (`log.jsonl`), estado del ciclo (`state.json`), registro de costos (`billing-ledger.json`), matriz de trazabilidad y reporte final (`final-report.json`), asegurando el control sobre el consumo de tokens y evitando drift de requerimientos.

---

## 2. Arquitectura del Sistema

La arquitectura del sistema se divide claramente en dos capas: **La Fábrica Agéntica (Infraestructura de Desarrollo)** y **El Sistema ERP Destino (PROYECTO CINCO)**.

### 2.1 Visión General de la Fábrica (ARNES)

La fábrica opera mediante un **Orquestador de Ciclo de 12 Pasos** que guía el proceso a través de un grafo de fases (`OrchestratorGraph`). Sin embargo, el orquestador no realiza el trabajo técnico directo ni llama a los LLM. Toda acción técnica es delegada a un agente a través del **Arnés de Contención (HarnessRunner)**, que es la **única puerta de entrada y salida autorizada**.

```
       [ Requerimiento / Work Order ]
                     │
                     ▼
             OrchestratorGraph
                     │
   ┌─────────────────┴─────────────────┐
   │         harness.run_agent()       │  <── Puerta Única (ARNES)
   │  ┌─────────────────────────────┐  │
   │  │        AgentRegistry        │  │
   │  │        ToolRegistry         │  │
   │  │        PolicyEngine         │  │
   │  │       ContextManager        │  │
   │  │         MemoryGate          │  │
   │  │        BudgetManager        │  │
   │  │       ValidatorChain        │  │
   │  └─────────────────────────────┘  │
   └─────────────────┬─────────────────┘
                     │
                     ▼
           [ Artefactos y Código ]
           - Backend FastAPI
           - Frontend Next.js / Tailwind
           - Tests Pytest
           - Bitácoras y Reportes
```

### 2.2 Componentes Principales de la Fábrica con Arnés

1. **HarnessRunner (`fabrica/harness.py`):** Es la clase central que expone el método estricto `run_agent(agent_id, state)`. Ningún agente puede ejecutar herramientas o llamar a la API del LLM de forma independiente; todo pasa por este arnés.
2. **AgentRegistry (`fabrica/registries.py`):** Catálogo cerrado de agentes de software especializados (ej. `agent.spec`, `agent.architecture_plan`, `agent.implementation`, `agent.qa`, `agent.security_policy`, `agent.frontend_design_system`, etc.). Define su propósito y sus herramientas/permisos permitidos.
3. **ToolRegistry (`fabrica/registries.py` y `fabrica/tools.py`):** Allowlist inmutable de herramientas parametrizadas. Cada herramienta tiene un esquema JSON estricto (`input_schema`, `output_schema`) que previene inyecciones de código.
4. **PolicyEngine (`fabrica/policy.py`):** Evalúa políticas en modo *deny-by-default*. Bloquea ejecuciones peligrosas (como comandos de consola no autorizados o accesos a secretos) y levanta solicitudes de aprobación humana (`ApprovalRequest`) cuando detecta efectos secundarios (*side effects*).
5. **ContextManager (`fabrica/context.py`):** Construye paquetes mínimos de contexto (`context-pack.json`) recuperados a través de RAG localizado. Evita pasar archivos y repositorios completos para optimizar el tamaño de ventana de contexto del LLM y reducir los costos de tokens.
6. **MemoryGate (`fabrica/memory.py`):** Filtra y procesa los registros de memoria (`Aprendizaje.md`). Aísla la memoria de la fábrica global de la memoria local del proyecto. Excluye registros marcados como contaminados (*tainted*), sospechosos o expirados (según su TTL).
7. **BudgetManager (`fabrica/budget.py`):** Mide dinámicamente los tokens consumidos (de entrada, salida, razonamiento y caché) y los costos en USD de cada llamada. Posee *circuit breakers* que pausan la ejecución de la fábrica si se excede el presupuesto límite configurado.
8. **ValidatorChain (`fabrica/validators.py`):** Cadena de validadores (ej. de esquema JSON, de evidencia recuperada, de seguridad, de presupuesto) que inspecciona la salida generada por el agente antes de que sea aceptada. Si falla un validador crítico, el ciclo es rechazado y reintentado o pausado.
9. **Observability & Storage (`fabrica/storage.py`):** Genera bitácoras y registros inmutables de auditoría como `state.json`, `log.jsonl`, `billing-ledger.json` y la matriz de trazabilidad.

---

## 3. Ejecución del Workflow: Caso Práctico (PROYECTO CINCO)

La fábrica ha sido aplicada para desarrollar el **PROYECTO CINCO**, que consiste en un **Sistema ERP Web Pequeño** con las siguientes especificaciones y módulos funcionales:

### 3.1 ¿En qué consiste el Proyecto?
El proyecto ERP incluye:
* **Módulo 1: Autenticación (Auth):** Control de acceso basado en roles (RBAC) con tokens JWT (login, refresh, logout, cambio de contraseña).
* **Módulo 2: Clientes y Créditos (Customers):** CRUD de clientes, gestión de contactos y asignación de límites de crédito comercial.
* **Módulo 3: Catálogo de Productos (Products):** Gestión de productos, categorías y unidades de medida.
* **Módulo 4: Inventarios y Bodegas (Inventory):** Gestión de stocks físicos, movimientos de entrada/salida, transferencias entre bodegas, ajustes y conteos físicos.
* **Módulo 5: Ventas (Sales):** Cotizaciones, órdenes de venta, despacho de mercancía, registro de pagos y anulaciones.
* **Módulo 6: Devoluciones (Returns):** Flujo de solicitud, aprobación, recepción en bodega y emisión de notas de crédito.
* **Módulo 7: Compras (Purchases):** Catálogo de proveedores, órdenes de compra, recepción de mercancías y registro de facturas recibidas.
* **Módulo 8: Producción (Production):** Estructura de listas de materiales (BOM), órdenes de producción, consumos de materia prima y cierre de órdenes.
* **Módulo 9: Facturación y Cobros (Billing):** Emisión de facturas comerciales, notas de crédito/débito y conciliación de pagos.
* **Módulo 10: Dashboard y Alertas:** Resúmenes analíticos del negocio y generación de logs de alertas de correo por stock bajo o sobregiro.

### 3.2 Flujo Operativo Ejecutado por la Fábrica
El workflow transita por las fases del grafo de orquestación, logrando la trazabilidad total:
1. **Intake / Constitución (`agent.spec`):** Valida la orden de trabajo (`work_order.json`). Genera la constitución con reglas de no invención y dry-run.
2. **Specify / Clarify (`agent.spec`):** Define el alcance exacto (incluye/excluye) en `spec.md` y documenta aclaraciones sobre la arquitectura.
3. **Checklist (`agent.spec`):** Valida las condiciones previas al diseño y asegura que se cumplan las políticas de la fábrica.
4. **Context / Plan (`agent.context_rag` y `agent.architecture_plan`):** Construye la base de evidencias RAG y diseña el plan técnico y de riesgos (`plan.md` y `risk-register.md`).
5. **Tasks (`agent.spec`):** Descompone la arquitectura en tareas atómicas y las vuelca en `TASKS.md` y `traceability-matrix.md`.
6. **Design System & UX (`agent.frontend_design_system` y `agent.ux_accessibility`):** Genera la guía de diseño visual (`DESIGN_SYSTEM.md`), las paletas de colores accesibles, reglas de copy y la matriz responsive en `responsive-matrix.json`.
7. **Implementation (`agent.implementation`):** Traduce el backlog en código de backend (routers de FastAPI, modelos SQLAlchemy y esquemas Pydantic) y componentes frontend correspondientes, generando reportes y patches de implementación dry-run.
8. **Validation & QA (`agent.tests_coverage`, `agent.security_policy` y `agent.frontend_visual_qa`):** Diseña y ejecuta la suite de pruebas unitarias (`test-plan.json` y `test_report.json`), realiza auditoría de seguridad para evitar fuga de secretos (`security-review.md`) y audita el QA visual del frontend (`visual-qa-report.json`).
9. **Observability & Close (`agent.devops_observability`, `agent.cost_optimizer` y `agent.documentation`):** Escribe el manual de operabilidad (`RUNBOOK.md`), consolida los costos reales del LLM en `cost-report.json`, genera el reporte final (`final-report.json`) y prepara el handoff seguro en `RUN_STATE.md`.

---

## 4. Diferencia Crítica: Fábrica Con Arnés vs. Sin Arnés

Una de las contribuciones conceptuales y operativas más importantes de esta actividad es la comprensión de la contención agéntica. Las diferencias estructurales de operar con y sin arnés se detallan a continuación:

| Dimensión | Fábrica Sin Arnés (Agencia Libre) | Fábrica Con Arnés (ARNES / Contención) |
|---|---|---|
| **Punto de Ejecución** | El agente se ejecuta de manera directa y libre (`agent.run()`). Puede llamar a la API del LLM o invocar herramientas sin intermediarios. | **Puerta Única Obligatoria (`harness.run_agent`)**. Ningún agente interactúa directamente con el LLM ni con el sistema de archivos externo sin pasar por el arnés. |
| **Control de Herramientas** | El agente decide qué herramientas usar en su prompt. Puede intentar usar comandos de sistema peligrosos o scripts externos arbitrarios. | **Allowlist en `ToolRegistry`**. El arnés carga únicamente las herramientas autorizadas para el rol del agente. Validaciones estrictas de esquemas de entrada y salida previenen comportamientos inesperados o inyecciones de prompts. |
| **Gobernanza de Seguridad** | No hay filtros centrales. El agente puede leer variables de entorno con tokens, modificar configuraciones del sistema operativo o escribir en producción. | **PolicyEngine (*deny-by-default*)**. Cualquier efecto secundario (*side effect*) crítico es bloqueado en dry-run y se genera un requerimiento de aprobación humana (`ApprovalRequest`). |
| **Presupuesto y Tokens** | Los agentes pueden entrar en bucles infinitos de llamadas o consumir millones de tokens procesando archivos inmensos sin control de costos. | **BudgetManager y Circuit Breakers**. Monitoreo en tiempo real de tokens de entrada, salida, razonamiento y caché. Detiene el ciclo inmediatamente si excede el presupuesto en USD establecido en la orden de trabajo. |
| **Calidad y Consistencia** | La salida del LLM se escribe directamente en los archivos. Errores de sintaxis, falta de campos o alucinaciones dañan el codebase de inmediato. | **ValidatorChain Automatizada**. Antes de retornar cualquier salida al orquestador, se validan los esquemas JSON, la presencia de evidencia verídica, la seguridad y la cobertura del código. |
| **Gobernanza de Memoria** | La memoria se lee/escribe en un único contexto acumulado que se pasa en cada llamada al LLM, encareciendo y contaminando el prompt. | **MemoryGate Aislada**. Lee memorias segmentadas con ámbito específico (fábrica vs. proyecto), con control de tiempo de vida (TTL) y marcas de contaminación (*taint*) que aíslan la información no aprobada o sospechosa. |
| **Trazabilidad** | El proceso es una caja negra. No es posible auditar por qué se modificó un archivo o qué fragmento de documentación justificó una decisión. | **Matriz de Trazabilidad y Evidencia**. Cada decisión técnica crítica del agente debe citar un `evidence_id` asociado a un fragmento inmutable recuperado por el RAG (`context-pack.json`), el cual se vincula directamente a un `task_id` y a un requisito del negocio. |

---

## 5. Conclusiones y Propuestas de Mejora

### 5.1 Conclusiones
* **Predecibilidad y Seguridad:** Operar la fábrica sobre el **PROYECTO CINCO** mediante **ARNES** demostró que es posible programar y estructurar sistemas de software complejos de forma segura y predecible. La contención agéntica elimina los riesgos de costos desmedidos y de código destructivo.
* **Trazabilidad sin Fricciones:** La generación automatizada del `traceability-matrix.md` y `final-report.json` asocia directamente cada línea de código escrita con un requerimiento verificado de la especificación técnica, facilitando los procesos de auditoría y revisión de calidad.
* **Gobernanza de Costos:** El uso del catálogo de precios oficial y la simulación/estimación local garantizan que el desarrollador posea un control absoluto del presupuesto antes de realizar llamadas productivas al modelo de lenguaje.

### 5.2 Propuestas de Mejora
1. **Automatización de GitLab (CI/CD real):** Integrar de forma directa el validador del pipeline de CI/CD para que el arnés ejecute pruebas dentro de contenedores efímeros aislados (Docker) y envíe reportes de cobertura directamente al repositorio remoto tras la aprobación humana del PR.
2. **Reranking Contextual Dinámico:** Mejorar el `ContextManager` incorporando modelos de reranking ligeros a nivel local que permitan priorizar fragmentos de código de gran longitud basándose en la similitud semántica con el archivo de la tarea, optimizando aún más el consumo de tokens en fases de refactorización.
3. **Interfaz Gráfica para Aprobaciones:** Diseñar un panel web básico de operabilidad donde el usuario pueda revisar las solicitudes de aprobación pendientes del `PolicyEngine` (cambios en archivos, ejecuciones de bases de datos o incrementos de presupuesto) y aprobarlas con un solo clic.

---

## 6. Evidencia de Operación de la Fábrica

Como evidencia de la ejecución del workflow de la fábrica bajo arnés, el sistema genera los siguientes artefactos en el workspace:
* [state.json](file:///c:/Users/Ainsi/Desktop/proyectos/espe3-S_10/state.json): Registro del estado del orquestador con firmas de fases y hashes.
* [log.jsonl](file:///c:/Users/Ainsi/Desktop/proyectos/espe3-S_10/log.jsonl): Bitácora cronológica inmutable de eventos de agentes y validadores.
* [billing-ledger.json](file:///c:/Users/Ainsi/Desktop/proyectos/espe3-S_10/billing-ledger.json): Ledger detallado del consumo de tokens y costos estimados por fase.
* [traceability-matrix.md](file:///c:/Users/Ainsi/Desktop/proyectos/espe3-S_10/traceability-matrix.md): Mapeo completo de requerimientos, tareas, evidencias y archivos modificados.
* [final-report.json](file:///c:/Users/Ainsi/Desktop/proyectos/espe3-S_10/final-report.json): Cierre formal del run que expone la lista de archivos creados, costos finales y próximos pasos seguros.
