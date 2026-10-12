# Sistema de Gestión — Colegio Mixto Presbítero "Julio González Celis"

> **Disparador:** cuando el usuario escriba **"Dale rey desarrolla"** (o algo equivalente), lee este archivo completo,
> luego `docs/PLAN.md`, y ejecuta las fases en orden. Al terminar cada fase: corre los tests, marca los checks en
> `docs/PLAN.md`, haz commit en git y continúa con la siguiente SIN pedir permiso, salvo que haya una
> **decisión pendiente** (ver sección al final) que bloquee el trabajo. Si no bloquea, usa el valor por defecto indicado.

## 1. Qué es esto

Sistema **local, de escritorio-web, para una sola PC** (la de la directora) de un colegio de nivel básico en Guatemala.
Corre sin internet, con base de datos en un solo archivo, y se entrega como **instalador de Windows** que se lleva en USB.

Registra:
1. **Estudiantes** actuales y antiguos (con responsables, contactos, direcciones, historial por año).
2. **Docentes y administrativos** con los cursos que imparten.
3. **Asistencia** por grado/jornada/mes y **notas** por grado/materia/unidad.
4. **Mensualidades** (inscripción + enero a octubre) por estudiante.
5. **Reportes imprimibles** con el encabezado y escudo del colegio.

Todo se ingresa **manualmente** por 1–2 usuarios. No hay portal para padres ni acceso por internet.

## 2. Principios (en orden de prioridad)

1. **No perder datos jamás.** Es la prioridad #1, por encima de funciones y estética. Ver `docs/SEGURIDAD_Y_RESPALDOS.md`.
2. **KEEP IT SIMPLE.** Usuaria no técnica. Pocas pantallas, textos claros en español, botones grandes, cero jerga.
   Si dudas entre una solución simple y una "elegante", elige la simple. No agregues librerías, apps ni features que no estén en el plan.
3. **Bonito y funcional.** Django Admin con `django-unfold` + 3 vistas propias (asistencia, notas, pagos). Sin SPA, sin React.
4. **Funciona 100% offline.** Prohibido cargar fuentes, CSS, JS o imágenes desde CDN/internet. Todo va empaquetado.
5. **Instalable por USB** en una PC Windows sin Python ni nada previo. Ver `docs/EMPAQUETADO.md`.

## 3. Stack (no cambiar sin avisar)

- Python 3.12 (64-bit) · Django 5.2 LTS · SQLite · `django-unfold` (UI del admin) · `django-simple-history` (auditoría)
- `waitress` como servidor (no `runserver` en producción) · `openpyxl` para exportar Excel
- HTMX **opcional** y servido localmente (archivo en `static/`), solo si simplifica asistencia/notas. Si no, JS vanilla.
- Tests con `pytest` + `pytest-django`
- Empaquetado: PyInstaller (`--onedir`, NO `--onefile`) + Inno Setup para el `Setup.exe`
- Plataforma objetivo: **Windows 10/11 64-bit**. El desarrollo se hace en **macOS** (y debe funcionar también en Windows); el build final se hace en Windows, normalmente con GitHub Actions (`.github/workflows/build-windows.yml`). No uses nada exclusivo de Windows fuera de las rutas congeladas del launcher (`ctypes.windll` va protegido con try/except) y mantén `build.bat` con saltos de línea CRLF y **sin `pause`** (corre sin interacción en CI).

## 4. Estructura esperada del repo

```
colegio-sistema/
├── CLAUDE.md                  ← este archivo
├── docs/                      ← plan, modelos, seguridad, empaquetado, referencia
├── assets/escudo_colegio.png  ← escudo oficial (usar en login, sidebar y reportes)
├── manage.py
├── config/                    ← proyecto Django (settings.py, urls.py, wsgi.py)
├── colegio/                   ← única app: models, admin, views, templates, reports, services
│   ├── models.py              ← implementar a partir de docs/referencia/models_referencia.py
│   ├── admin.py
│   ├── views/                 ← asistencia.py, notas.py, pagos.py, respaldos.py, setup.py
│   ├── services/              ← respaldos.py, exportar_excel.py, codigos.py
│   ├── templates/ · static/   ← todo local, sin CDN
│   └── tests/
├── launcher.py                ← punto de entrada del .exe (ver docs/referencia/launcher_referencia.py)
├── colegio.spec               ← spec de PyInstaller
├── installer/colegio.iss      ← script de Inno Setup
├── build.bat                  ← build completo en Windows (venv → tests → pyinstaller → inno)
└── requirements*.txt
```

## 5. Reglas de datos y seguridad (NO NEGOCIABLES)

- **Nunca borrado físico** de Estudiante, Docente, Matrícula, Pago, Nota ni Asistencia. Se usa `estado`/`activo`/`anulado`.
  En el admin, `has_delete_permission` devuelve `False` para esos modelos. Todas las FK con `on_delete=PROTECT`.
- **Auditoría:** `HistoricalRecords()` en Estudiante, Responsable, Docente, Matrícula, Pago y Nota. Debe verse "quién cambió qué y cuándo".
- **Servidor solo en `127.0.0.1`** (nunca `0.0.0.0`). `ALLOWED_HOSTS = ["127.0.0.1", "localhost"]`. `DEBUG = False`.
- `SECRET_KEY` se genera la primera vez y se guarda en `datos/secret.key`. Jamás va en el repo.
- **Sin contraseñas por defecto.** En el primer arranque, si no hay usuarios, mostrar una pantalla de "Configuración inicial"
  para crear la cuenta de la directora (solo disponible mientras no exista ningún usuario).
- Dos roles (grupos de Django): **Directora** (todo, incluye usuarios y respaldos) y **Secretaria** (agregar/editar/ver; sin borrar, sin usuarios).
- Sesión expira tras 2 h de inactividad. Validadores de contraseña de Django activos (mínimo 8).
- **SQLite:** `PRAGMA foreign_keys=ON`, `synchronous=FULL`, `busy_timeout=5000`, `journal_mode=DELETE` (un solo archivo `colegio.db`).
- **Respaldos automáticos** con la API de backup de SQLite (nunca copiando el archivo en caliente). Detalles en `docs/SEGURIDAD_Y_RESPALDOS.md`.
- **La carpeta de datos vive FUERA de la carpeta de la aplicación** para que actualizar o desinstalar nunca toque los datos.
- Antes de **cualquier migración** en el arranque: respaldo automático + `PRAGMA integrity_check`. Si la migración falla, restaurar y avisar.
- Son datos de **menores de edad**: no enviar nada a internet, sin telemetría, sin logs que contengan CUI ni nombres completos.

## 6. Convenciones de código

- Todo el código en inglés **excepto** nombres de modelos/campos de dominio, que van en español como en `docs/referencia/models_referencia.py`
  (`Estudiante`, `Matricula`, `primer_apellido`...) porque coinciden con el vocabulario del colegio. Textos de UI, mensajes y `verbose_name` en español.
- `LANGUAGE_CODE = "es"`, `TIME_ZONE = "America/Guatemala"`, `USE_TZ = True`, moneda: Quetzales (`Q 1,250.00`), fechas `dd/mm/aaaa`.
- Dinero: `DecimalField(max_digits=8, decimal_places=2)`. Nunca `float`.
- Rutas con `pathlib`. Todo acceso a archivos de datos pasa por una única función `get_data_dir()` (ver launcher de referencia),
  que resuelve distinto en desarrollo vs. ejecutable congelado (`sys.frozen` / `sys._MEIPASS`).
- Vistas simples basadas en funciones. Sin DRF, sin APIs. Sin Celery. Sin Docker.
- Cada función de servicio importante lleva test. Mínimo obligatorio de tests en `docs/PLAN.md`.
- Commits pequeños, mensajes en inglés imperativo ("Add Pago model").

## 7. Reportes imprimibles

Encabezado en todos: escudo + **Colegio Mixto Presbítero "Julio González Celis"** + Jornada / Ciclo / Grado.
Tamaño **Carta**, CSS `@media print`/`@page`. Asistencia en horizontal (31 días caben). Los 3 formatos base están en
`docs/CAMPOS_ORIGINALES.md` (Calificaciones, Asistencia, Pagos). Botón "Imprimir" y botón "Exportar a Excel" en cada uno.

## 8. Cómo trabajar

1. Lee `docs/PLAN.md` y avanza por fases. Una fase = código + tests + commit.
2. Usa los archivos de `docs/referencia/` como **punto de partida** (modelos, launcher): son correctos en intención pero no han sido ejecutados; pruébalos y corrígelos.
3. Verifica con datos de prueba: crea un comando `python manage.py cargar_demo` que genere ~40 estudiantes, 6 docentes, 1 ciclo, pagos y asistencia ficticios (nombres inventados, jamás datos reales).
4. Al final de cada fase, ejecuta: `pytest -q` y `python manage.py check --deploy`.
5. Si una decisión no está en estos documentos y afecta datos o seguridad, pregunta. Si es solo de estética, decide tú.
6. Mantén `docs/PLAN.md` actualizado (marca `[x]`) y escribe `docs/MANUAL_DIRECTORA.md` (1–2 páginas, con capturas o pasos numerados) en la Fase 6.

## 9. Decisiones pendientes (usar el valor por defecto, y dejar el valor configurable)

| # | Tema | Valor por defecto | Dónde se configura |
|---|------|-------------------|--------------------|
| 1 | Unidades de calificación por año | 4 unidades | constante `UNIDADES_POR_CICLO` en `settings.py` |
| 2 | Escala de punteo | 0 a 100, 2 decimales | constantes `NOTA_MIN`, `NOTA_MAX` |
| 3 | Nota mínima para aprobar (solo para resaltar en rojo) | 60 | constante `NOTA_APROBACION` |
| 4 | Meses de cobro | Inscripción + enero a octubre | enum `Concepto` en `models.py` |
| 5 | Formato del código de estudiante si se deja vacío | `AAAA-NNNN` (año de ingreso + secuencia) | `services/codigos.py` |
| 6 | Código de docente | `D-NNN` | `services/codigos.py` |
| 7 | Ruta secundaria de respaldos (USB / otra carpeta) | vacía | pantalla "Respaldos" → guardada en `datos/config.ini` |
| 8 | Notas: una sola columna de punteo por unidad (el total) | sí; detalle por actividad queda para versión 2 | `Nota.punteo` |

## 10. Definición de "terminado"

- Todos los checks de `docs/PLAN.md` marcados, tests en verde, `check --deploy` sin errores críticos.
- Se puede ejecutar `build.bat` en una PC Windows limpia con Python 3.12 y produce `Setup_ColegioJGC.exe`.
- El `Setup.exe` instalado en una PC Windows **sin Python**: crea acceso directo en el escritorio, abre el navegador, pide crear la cuenta de la directora, y todo funciona sin internet.
- Prueba de fuego de datos: instalar → cargar demo → desinstalar → reinstalar → **los datos siguen ahí**. Matar el proceso a mitad de un guardado → al reabrir no hay corrupción.
