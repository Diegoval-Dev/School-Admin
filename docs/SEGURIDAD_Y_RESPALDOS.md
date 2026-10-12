# Seguridad y respaldos

Objetivo: **que la información del colegio no se pierda ni se exponga**, aun con un mal uso (cierre brusco, apagón, borrado accidental, USB perdida, disco dañado).

## 1. Amenazas y defensa

| Amenaza | Defensa |
|---|---|
| Apagón o cierre brusco durante un guardado | SQLite transaccional + `synchronous=FULL`. Al arrancar: `PRAGMA integrity_check`; si falla, se ofrece restaurar el último respaldo bueno. |
| Borrar un registro por error | No existe borrado físico. Estados (retirado/graduado), anulación de pagos con motivo, `on_delete=PROTECT`. |
| Editar mal un dato | Historial de cambios (`simple_history`): quién, cuándo y valor anterior. Se puede revertir desde el admin. |
| Falla del disco / PC dañada | Respaldo secundario en USB/otra carpeta + exportación a Excel. Aviso si el respaldo externo tiene más de 7 días. |
| Una actualización rompe la base | Respaldo + `integrity_check` antes de cada migración; si falla, restauración automática. |
| Desinstalar/reinstalar por accidente | `datos/` y `respaldos/` viven fuera de la app y el desinstalador no los toca. |
| Acceso no autorizado en la PC | Login obligatorio, servidor solo en `127.0.0.1`, sesión que expira, roles (Directora / Secretaria). Recomendar contraseña de Windows y BitLocker. |
| Filtración de datos de menores | Sin internet, sin telemetría, sin CDN, sin datos personales en logs. |
| Malware / ransomware | Copia en USB que no queda conectada. Recomendar desconectar la USB tras respaldar. |

## 2. Dónde viven los datos

```
C:\ColegioJGC\
├── app\            ← programa (se puede borrar y reinstalar sin riesgo)
├── datos\
│   ├── colegio.db  ← LA base de datos (un solo archivo)
│   ├── secret.key  ← clave interna generada en el primer arranque
│   └── config.ini  ← ruta secundaria de respaldos, preferencias
└── respaldos\      ← respaldos automáticos con fecha
```

Durante el desarrollo: `./datos` y `./respaldos` dentro del repo (ya están en `.gitignore`).

## 3. Respaldo correcto (nunca copiar el .db "en caliente")

Usar siempre la API de backup de SQLite, que genera una copia consistente aunque la app esté en uso:

```python
import sqlite3
from datetime import datetime
from pathlib import Path

def respaldar(db_path: Path, destino_dir: Path, etiqueta: str = "auto") -> Path:
    destino_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    tmp = destino_dir / f".tmp-{ts}.db"
    final = destino_dir / f"colegio-{ts}-{etiqueta}.db"
    src = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    dst = sqlite3.connect(tmp)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    chk = sqlite3.connect(tmp)
    try:
        ok = chk.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        chk.close()
    if not ok:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("El respaldo no pasó la verificación de integridad.")
    tmp.replace(final)          # atómico: nunca queda un respaldo a medias
    return final
```

### Cuándo se respalda
1. Al **iniciar** el sistema (antes de migrar).
2. Al **cerrar** limpiamente (botón "Cerrar sistema").
3. Cada **2 horas** con la app abierta (hilo en segundo plano; solo si hubo cambios desde el último).
4. Antes de **cualquier migración** y antes de **restaurar**.
5. Manual: botón "Respaldar ahora".

### Rotación (el disco es barato, los datos no)
Conservar: todos los de los últimos 7 días · 1 por día durante 30 días · 1 por mes durante 24 meses.
**Nunca borrar los 5 más recientes**, pase lo que pase. Los respaldos "antes de restaurar" y "antes de migrar" no se rotan en 90 días.

### Copia secundaria (USB u otra carpeta)
- Ruta configurable en la pantalla "Respaldos" (guardada en `config.ini`).
- Tras cada respaldo se copia a la ruta secundaria **si existe en ese momento** (la USB puede no estar conectada: no es error, solo se anota).
- En el Inicio: banner amarillo si el último respaldo externo tiene más de 7 días ("Copia tu respaldo a la USB"), rojo si más de 30.
- Botón **"Descargar respaldo (.zip)"** que incluye `colegio.db` + `colegio_estudiantes.xlsx` (exportación legible).

## 4. Restaurar

- Acceso directo "Restaurar respaldo" (llama a `ColegioJGC.exe --restaurar`) que muestra la lista de respaldos y pide elegir uno.
- Pasos internos: verificar integridad del elegido → **respaldar el estado actual** como `antes-de-restaurar-FECHA.db` → reemplazar `colegio.db` con `os.replace` → borrar archivos `-journal` huérfanos → arrancar.
- Doble confirmación en pantalla ("Se perderán los cambios hechos después de ese respaldo").
- Debe poder restaurarse **también desde un .db copiado de la USB** (botón "Elegir archivo…").

## 5. Verificación al arrancar

1. Adquirir bloqueo de instancia única (ver §7).
2. Si existe `colegio.db`: `PRAGMA integrity_check`. Si no es `ok` → mostrar pantalla de rescate: "La base de datos tiene un problema. Restaurar el respaldo más reciente (FECHA)". No continuar con una base dañada.
3. Respaldo previo a migración → `migrate`. Si falla: restaurar ese respaldo y mostrar un mensaje claro (no un traceback).

## 6. Configuración Django (checklist)

- `DEBUG=False`, `ALLOWED_HOSTS=["127.0.0.1","localhost"]`.
- `SECRET_KEY` desde `datos/secret.key` (se crea en el primer arranque con `secrets.token_urlsafe(64)`).
- `SESSION_COOKIE_AGE=7200`, `SESSION_SAVE_EVERY_REQUEST=True`, `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE="Lax"`.
- `CSRF_TRUSTED_ORIGINS=["http://127.0.0.1:*","http://localhost:*"]` (ajustar al puerto real).
- Validadores de contraseña por defecto de Django. Sin usuario/contraseña por defecto.
- Cabeceras: `X_FRAME_OPTIONS="DENY"`, `SECURE_CONTENT_TYPE_NOSNIFF=True`. (HTTPS no aplica en loopback.)
- Logging a archivo en `datos/logs/` con rotación; **sin** nombres completos, CUI ni teléfonos en los mensajes.
- `python manage.py check --deploy` sin errores relevantes (ignorar los de HTTPS y explicar por qué no aplican).
- Revisar que ninguna plantilla cargue recursos externos (`grep -R "http" templates/ static/` y revisar el tráfico en el navegador con la red desconectada).

## 7. Instancia única

Evita dos copias abriendo la misma base. Al iniciar, intentar `bind` a `127.0.0.1:47653` (puerto de bloqueo) y mantenerlo abierto. Si ya está ocupado: leer `datos/puerto.txt`, abrir el navegador en esa dirección y salir sin tocar nada.

## 8. Tests obligatorios (Fase 5)

1. El respaldo genera un archivo válido, abrible y con los mismos datos.
2. Un respaldo "corrupto" (archivo truncado) es rechazado y el original queda intacto.
3. Rotación: conserva lo esperado y nunca borra los 5 más recientes.
4. Restaurar crea primero `antes-de-restaurar-*` y deja la base igual al respaldo elegido.
5. Migración que falla (simulada) → se restaura automáticamente.
6. Segunda instancia es rechazada sin tocar la base.
7. Secretaria no puede borrar ni acceder a Usuarios/Respaldos.
8. Respaldo con la USB ausente no lanza error y queda anotado como "pendiente de copia externa".
