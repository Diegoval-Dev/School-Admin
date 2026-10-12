# Plan de desarrollo

Marca cada check `[x]` al completarlo. Una fase = código + tests + commit. No avances si los tests de la fase fallan.

---

## Fase 0 — Proyecto base
- [x] Crear `venv`, instalar `requirements-dev.txt`, `git init` (el `.gitignore` ya existe).
- [x] `django-admin startproject config .` y `python manage.py startapp colegio`.
- [x] `settings.py`: idioma `es`, zona `America/Guatemala`, `DEBUG=False` por defecto (variable de entorno `COLEGIO_DEBUG=1` solo para desarrollo), `ALLOWED_HOSTS` local, sesión 2 h, validadores de contraseña.
- [x] `get_data_dir()` y `get_resource_dir()` en `config/paths.py` (desarrollo: `./datos`; congelado: carpeta fuera de la app, ver `docs/EMPAQUETADO.md`). `DATABASES` apunta a `datos/colegio.db` con los PRAGMAs de `CLAUDE.md §5`.
- [x] `SECRET_KEY` autogenerada y persistida en `datos/secret.key`.
- [x] Instalar y configurar `unfold` y `simple_history`. Escudo en login y sidebar. Verificar que **no hay ninguna petición a internet** (revisar fuentes/íconos de Unfold; si alguno es remoto, empaquetarlo local).
- [x] pytest configurado; primer test "arranca y responde 200 en /login/".

## Fase 1 — Modelos y administración  (docs/referencia/models_referencia.py)
- [x] Implementar modelos de `docs/MODELOS.md` y migraciones iniciales.
- [x] Admin de **Estudiante** con inlines: Responsables (padre/madre/tutor), Contactos, Direcciones, Matrículas. Buscador por código, nombres, apellidos y documento. Filtros: estado, grado, jornada, ciclo.
- [x] Admin de **Docente** con inline de Asignaciones (curso, grado, ciclo). Admin de **Materia** y **CicloEscolar**.
- [x] Sin borrado físico: `has_delete_permission=False` y acción masiva de borrar removida. Estados: Activo / Retirado / Graduado.
- [x] Edad calculada (propiedad) y mostrada en el listado, nunca guardada.
- [x] Código autogenerado si se deja vacío (`services/codigos.py`).
- [x] Validación: CUI de 13 dígitos cuando el tipo es CUI; pasaporte alfanumérico; un estudiante no puede tener dos matrículas en el mismo ciclo.
- [x] Auditoría con `simple_history` visible en el botón "Historial" de cada registro.
- [x] Grupos y permisos: **Directora** y **Secretaria** (migración de datos que los crea). Pantalla de **configuración inicial** (crear la cuenta de la directora si no hay usuarios).
- [x] Comando `cargar_demo`.
- **Tests:** edad; unicidad de matrícula por ciclo; código autogenerado sin colisiones; `PROTECT` impide borrar estudiante con pagos; Secretaria no puede borrar.

## Fase 2 — Pagos (mensualidades)
- [x] Modelo `Pago` (una fila por concepto: Inscripción, Enero…Octubre). Un solo pago **no anulado** por matrícula+concepto.
- [x] Pantalla **Pagos**: elegir ciclo, grado y jornada → tabla estudiantes × (Inscripción, Ene…Oct). Celda verde = pagado (muestra monto/fecha), vacía/gris = pendiente. Clic en celda → registrar pago (monto, fecha, no. de recibo opcional).
- [x] **Anular** pago con motivo obligatorio (no se borra). Anulados no cuentan como pagados pero quedan en el historial.
- [x] Estado de cuenta por estudiante (todos sus pagos del ciclo, total pagado) y listado de **pendientes del mes**.
- [x] Reporte imprimible "Pagos" (formato en `docs/CAMPOS_ORIGINALES.md`) + exportar a Excel.
- **Tests:** no duplicar pago activo; anular permite volver a registrar; totales correctos con Decimal.

## Fase 3 — Asistencia
- [x] Pantalla **Asistencia**: elegir ciclo, grado, jornada y mes → cuadrícula estudiantes × días (1–31, solo días del mes). Clic cicla entre: vacío → Presente (✓) → Ausente (✗) → Excusa (E). Guardado automático por celda o botón "Guardar" grande (elegir lo más simple y fiable).
- [x] Solo estudiantes con matrícula activa en ese ciclo/grado/jornada. Fines de semana resaltados; en jornada "Fin de semana" mostrar solo sábados/domingos.
- [x] Totales por estudiante (presentes, ausentes, excusas) al final de la fila.
- [x] Reporte imprimible (Carta horizontal) + Excel.
- **Tests:** una asistencia por matrícula+fecha; cambio de estado; solo matrículas activas aparecen.

## Fase 4 — Notas
- [x] Pantalla **Notas**: elegir ciclo, grado, materia y docente → tabla estudiantes × unidades (1–4) + TOTAL/PROMEDIO. Validar rango `NOTA_MIN..NOTA_MAX`. Notas bajo `NOTA_APROBACION` en rojo.
- [x] Navegación con Tab/Enter entre celdas para captura rápida; guardar con botón claro.
- [x] Reporte imprimible "Calificaciones" (con docente, materia y fecha) + Excel.
- **Tests:** unicidad (matrícula, materia, unidad); rango válido; promedio correcto.

## Fase 5 — Respaldos y seguridad  (docs/SEGURIDAD_Y_RESPALDOS.md)
- [x] `services/respaldos.py`: respaldo con `sqlite3.Connection.backup()`, verificación con `integrity_check`, rotación, copia secundaria.
- [ ] Respaldo automático al iniciar, al cerrar limpiamente y cada 2 h con la app abierta. Respaldo previo a toda migración.
- [ ] Pantalla **Respaldos** (solo Directora): lista, "Respaldar ahora", "Descargar respaldo (.zip)", ruta secundaria (USB), aviso en la pantalla de inicio si el último respaldo externo tiene > 7 días.
- [ ] **Restaurar:** script `restaurar_respaldo.py` / acceso directo "Restaurar respaldo" del instalador. Antes de restaurar, respalda el estado actual; confirma con doble aviso.
- [x] **Exportar todo a Excel** (un libro con una hoja por tabla principal) como respaldo legible por humanos.
- [ ] Al arrancar: `integrity_check`; si falla, ofrecer restaurar el último respaldo bueno automáticamente.
- [ ] Bloqueo de instancia única (si ya está corriendo, abrir el navegador en la instancia existente y salir).
- **Tests (obligatorios):** respaldo produce archivo válido y restaurable; rotación conserva lo correcto y nunca borra los 5 más recientes; restaurar guarda copia previa; migración fallida → restaura; doble instancia bloqueada.

## Fase 6 — Reportes, pulido y manual
- [ ] Inicio: buscador global de estudiantes, accesos rápidos grandes (Estudiantes, Pagos, Asistencia, Notas, Docentes, Respaldos), alertas (respaldo viejo, pagos pendientes del mes).
- [ ] Reportes extra: listado de estudiantes por grado/jornada, estudiantes retirados/graduados (históricos), ficha del estudiante imprimible.
- [ ] Revisión visual en pantallas 1366×768 y 1920×1080. Textos claros, sin jerga. Mensajes de error comprensibles.
- [ ] `docs/MANUAL_DIRECTORA.md`: instalar, abrir, crear usuarios, registrar estudiante/pago/asistencia/notas, hacer y restaurar respaldos, qué hacer si algo falla. 1–2 páginas, pasos numerados.
- [ ] Opcional (solo si sobra tiempo): tarifas por grado para autocompletar el monto del pago.

## Fase 7 — Empaquetado e instalador  (docs/EMPAQUETADO.md)
- [ ] `launcher.py` final: rutas congeladas, respaldo+migración, waitress en 127.0.0.1, puerto libre automático (8000→8010), abre navegador, instancia única, ícono de bandeja o ventana mínima con botón "Cerrar sistema" (elegir lo más simple).
- [ ] `colegio.spec` de PyInstaller `--onedir`, incluyendo templates, static, `unfold`, `simple_history`, escudo y migraciones (`collect_all`/`collect_data_files`).
- [ ] `installer/colegio.iss` (Inno Setup): instala en `C:\ColegioJGC\app`, crea `C:\ColegioJGC\datos` y `respaldos` **solo si no existen**, acceso directo en escritorio, el desinstalador **jamás** borra `datos`/`respaldos`, ícono con el escudo.
- [ ] `build.bat`: venv limpio → `pip install` → `pytest` → `pyinstaller` → `iscc` → `dist\Setup_ColegioJGC.exe`.
- [ ] **Pruebas en PC limpia sin Python** (VM o máquina real): instalar, primer arranque, crear cuenta, cargar datos, cerrar, reabrir, actualizar a una versión nueva (datos intactos), desinstalar/reinstalar (datos intactos), matar el proceso a mitad de guardado (sin corrupción), antivirus/SmartScreen (documentar cómo aprobar el instalador).
- [ ] Verificar que `.github/workflows/build-windows.yml` funcione: el workflow debe terminar en verde y dejar `Setup_ColegioJGC_*.exe` como artefacto descargable (`build.bat` no interactivo).
- [ ] Versión visible en pie de página y en el nombre del instalador (`version.txt`).

---

## Criterios de aceptación globales
1. Una persona sin conocimientos técnicos puede instalar, registrar un estudiante, un pago, una asistencia y una nota siguiendo solo el manual.
2. Ningún flujo normal permite borrar datos definitivamente.
3. Con la PC sin internet todo funciona y la app no intenta conectarse a nada.
4. Existe siempre al menos un respaldo verificado de las últimas 24 h y el sistema avisa si no hay copia externa reciente.
5. Actualizar o reinstalar nunca toca `datos/` ni `respaldos/`.
