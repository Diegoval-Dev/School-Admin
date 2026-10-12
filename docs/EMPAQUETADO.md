# Empaquetado e instalación por USB

Meta: un archivo **`Setup_ColegioJGC.exe`** que se copia a una USB, se ejecuta en la PC de la directora (sin Python ni nada instalado) y deja el sistema funcionando con un acceso directo en el escritorio.

## 1. Por qué este camino

- **PyInstaller `--onedir`** (carpeta), no `--onefile`: arranca más rápido, no descomprime en `%TEMP%` cada vez (menos riesgo con la base de datos) y los antivirus lo marcan menos.
- **Inno Setup** crea un instalador estándar de Windows (Siguiente → Siguiente → Instalar), maneja actualizaciones y **desinstala sin tocar los datos**.
- **El build se hace en Windows** (PyInstaller no compila cruzado). Hace falta: Python 3.12 64-bit, Inno Setup 6 (`iscc.exe` en el PATH).
- Sistema objetivo: **Windows 10 o 11, 64-bit**. (Python 3.12 no corre en Windows 7/8.)

## 2. Rutas (el punto donde más se rompe PyInstaller)

Todo acceso a archivos pasa por funciones en `config/paths.py`:

| Función | Desarrollo | Congelado (.exe) |
|---|---|---|
| `get_app_dir()` | raíz del repo | carpeta del `.exe` (`sys.executable`) |
| `get_data_dir()` | `./datos` | `C:\ColegioJGC\datos` (override: variable `COLEGIO_DATA_DIR`) |
| `get_backup_dir()` | `./respaldos` | `C:\ColegioJGC\respaldos` |
| recursos (templates/static) | los de Django normales | dentro de `_internal` (`sys._MEIPASS`), los encuentra Django si los paquetes están recolectados |

Reglas: **nunca** guardar nada escribible dentro de `app\`; nunca usar rutas relativas al directorio de trabajo; nunca asumir `__file__` de módulos fuera del bundle.

## 3. Archivos estáticos

Waitress no sirve estáticos. Usar **WhiteNoise** (agregar a `requirements.txt` y al middleware) y correr `collectstatic` en el build hacia `staticfiles/`, que se incluye en el bundle. Verificar que Unfold y el admin se vean completos **sin internet**.

## 4. Launcher (`launcher.py`)

Punto de entrada del `.exe`. Referencia: `docs/referencia/launcher_referencia.py`. Secuencia:

1. Bloqueo de instancia única (si ya corre → abrir navegador y salir).
2. Resolver rutas, crear `datos/` y `respaldos/` si no existen, generar `secret.key` si falta.
3. Modo `--restaurar` → flujo de restauración (ver `SEGURIDAD_Y_RESPALDOS.md §4`) y salir.
4. `integrity_check` → respaldo previo → `migrate` (con restauración si falla).
5. Elegir puerto libre (8000–8010), guardarlo en `datos/puerto.txt`.
6. Arrancar **waitress** en `127.0.0.1` y abrir el navegador por defecto en `http://127.0.0.1:PUERTO/`.
7. Hilo de respaldo cada 2 h. Endpoint protegido `POST /sistema/cerrar/` (botón "Cerrar sistema" en el menú): respalda, detiene waitress y termina el proceso.
8. Compilar con `--noconsole`. Los errores fatales se escriben en `datos/logs/` y se muestran en un cuadro de diálogo (`ctypes.windll.user32.MessageBoxW`), nunca una ventana en blanco.

## 5. PyInstaller (`colegio.spec`)

Puntos a cubrir (el spec se genera y se ajusta hasta que funcione en máquina limpia):

```
pyinstaller launcher.py --name ColegioJGC --noconsole --onedir --icon assets/icono.ico ^
  --collect-all unfold --collect-all simple_history --collect-all whitenoise ^
  --collect-submodules colegio --collect-submodules config ^
  --hidden-import waitress --hidden-import sqlite3 ^
  --add-data "colegio/templates;colegio/templates" ^
  --add-data "staticfiles;staticfiles" ^
  --add-data "assets;assets"
```

- Incluir **las migraciones** (las recoge `--collect-submodules colegio`; verificar que existan dentro del bundle).
- Crear `assets/icono.ico` desde `assets/escudo_colegio.png` con Pillow (script `tools/make_icon.py`, Pillow solo en dev).
- Si falta algo en runtime (`ModuleNotFoundError`, plantilla no encontrada), se resuelve con `--collect-all`/`--hidden-import`, no copiando archivos a mano.

## 6. Instalador (`installer/colegio.iss`, Inno Setup)

Requisitos del script:

- `AppId` fijo (un GUID propio, **nunca cambia**: así las actualizaciones reemplazan la instalación anterior).
- `PrivilegesRequired=admin` (para crear `C:\ColegioJGC`), `DefaultDirName=C:\ColegioJGC\app`.
- `[Dirs]`: `C:\ColegioJGC\datos` y `C:\ColegioJGC\respaldos` con permisos `users-modify` y flag **`uninsneveruninstall`**.
- `[Files]`: copia `dist\ColegioJGC\*` a `{app}`; **nunca** incluye `datos\`, `respaldos\` ni `*.db`.
- `[Icons]`: acceso directo en escritorio y menú inicio ("Sistema del Colegio") + "Restaurar respaldo" (`ColegioJGC.exe --restaurar`) en el menú inicio.
- `CloseApplications=yes` / `RestartApplications=no`: cierra la app si está abierta durante una actualización.
- `[UninstallDelete]`: solo archivos dentro de `{app}`. **Jamás** `datos` ni `respaldos`.
- Nombre de salida: `Setup_ColegioJGC_vX.Y.Z.exe`. Versión leída de `version.txt`.
- Al finalizar: casilla "Abrir el sistema ahora".

## 7. `build.bat`

```
1. rmdir build dist
2. python -m venv .venv-build  &&  pip install -r requirements-dev.txt
3. pytest -q                     (si falla, aborta)
4. python manage.py collectstatic --noinput
5. python tools/make_icon.py
6. pyinstaller colegio.spec
7. iscc installer\colegio.iss    →  dist\Setup_ColegioJGC_vX.Y.Z.exe
```

## 8. Prueba en máquina limpia (obligatoria antes de entregar)

Usar una VM de Windows 10/11 sin Python, o una PC real. Checklist:

- [ ] Instalar desde el `Setup.exe` copiado de una USB. Aparece el acceso directo.
- [ ] Primer arranque: abre el navegador, pide crear la cuenta de la directora, sin errores.
- [ ] Sin internet: todo se ve y funciona (íconos, fuentes, estilos).
- [ ] Cargar datos, cerrar con el botón, reabrir: datos intactos y se creó un respaldo.
- [ ] Doble clic al acceso directo con el sistema abierto: no abre una segunda instancia.
- [ ] Matar `ColegioJGC.exe` desde el Administrador de tareas en medio de guardar → reabrir sin corrupción.
- [ ] Instalar una versión nueva encima: datos intactos, se creó respaldo previo a migración.
- [ ] Desinstalar → reinstalar: **los datos siguen**.
- [ ] Restaurar un respaldo desde el acceso directo y desde un `.db` en la USB.
- [ ] Windows Defender no lo borra. Documentar el aviso de SmartScreen.

## 9. Avisos que verá la directora (documentarlos en el manual)

- **SmartScreen** ("Windows protegió su PC"): el instalador no está firmado digitalmente (cuesta dinero anual). Clic en **Más información → Ejecutar de todas formas**. Entregarlo en persona o desde una USB propia reduce el riesgo de confusión.
- **Firewall de Windows**: no debería preguntar porque solo escucha en `127.0.0.1`; si pregunta, **no** permitir acceso a redes públicas.
- **Antivirus**: si bloquea, agregar `C:\ColegioJGC\` como excepción.

## 10. Actualizaciones futuras

1. Subir `version.txt`, correr `build.bat`.
2. Copiar el nuevo `Setup` a la USB e instalar sobre el existente (mismo `AppId`).
3. Al abrir, el sistema respalda y migra solo. Si algo falla, restaura y avisa.
