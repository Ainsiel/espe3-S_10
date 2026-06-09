# Practicas permanentes

## Fuente incorporada
- source_path: /Volumes/KINGSTON/CODEX HD/FAbrica FULL UNO /buenas_practicas.md
- source_hash: sha256:7261892c7f559de0e9c42510dfc7e6a1c547ede95021510fdc55639d0da84d48
- estado: activo_permanente

## Reglas
- Construir simple primero y separar frontend, API, base de datos y workers.
- Frontend con Next.js, React, TypeScript, Tailwind CSS y shadcn/ui cuando el proyecto lo autorice.
- Validacion fuerte frontend/backend; no confiar en datos enviados por el cliente.
- Permisos reales por operacion; no depender solo de frontend.
- UI usable sin manual: claridad, consistencia, jerarquia, textos simples, estados claros.
- Un boton principal por pantalla; destructivos en rojo y con confirmacion.
- Formularios con label visible, validacion inmediata y errores accionables.
- Tablas administrativas con busqueda, filtros, ordenamiento, paginacion y acciones por fila.
- Toda pantalla cubre loading, empty, with_data, permission_denied, error y success.
- Paleta profesional por roles; no depender solo del color.
- Contraste WCAG AA: 4.5:1 texto normal, 3:1 texto grande e interfaz.
- Tipografia Inter/system-ui, texto normal minimo 16px y line-height 1.4-1.6.
- Responsive mobile-first con breakpoints y container queries cuando aplique.
- CI/CD con lint, formato, tests, tipos, secretos, vulnerabilidades y aprobacion manual para produccion.

## Aplicacion en cada proyecto
- El work_order independiente debe conservar estas reglas salvo excepcion aprobada y trazable.
- La memoria factory y la memoria project no se mezclan.
- El frontend concreto debe ejecutar lint, typecheck, tests, accesibilidad, responsive y QA visual cuando exista target renderizable.
- Ningun color, fuente, componente o patron destructivo se aprueba sin evidencia de contraste, estado, responsive y trazabilidad.
