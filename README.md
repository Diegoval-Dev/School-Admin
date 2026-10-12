# Kit de desarrollo — Sistema del Colegio "Julio González Celis"

## Cómo usarlo con Claude Code

1. Descomprime esta carpeta (por ejemplo en `C:\dev\colegio-sistema`).
2. Abre una terminal en la carpeta y ejecuta `claude`.
3. Escribe:  **Dale rey desarrolla**   (o el comando  `/desarrolla`).
   Claude Code lee `CLAUDE.md` automáticamente y sigue `docs/PLAN.md` fase por fase.

Comandos útiles dentro de Claude Code:
- `/desarrolla`  → avanza por todo el plan.
- `/fase 5`      → ejecuta solo una fase (ej. respaldos).
- `/revisar-seguridad` → auditoría de seguridad / pérdida de datos.

## Contenido

| Archivo | Para qué |
|---|---|
| `CLAUDE.md` | Instrucciones maestras, reglas no negociables, stack y decisiones |
| `docs/PLAN.md` | Plan en 8 fases con checklists y tests obligatorios |
| `docs/MODELOS.md` + `docs/referencia/models_referencia.py` | Modelo de datos y código de partida |
| `docs/SEGURIDAD_Y_RESPALDOS.md` | Cómo no perder ni filtrar datos |
| `docs/EMPAQUETADO.md` + `docs/referencia/launcher_referencia.py` | PyInstaller + instalador para USB |
| `docs/CAMPOS_ORIGINALES.md` | Lista original del colegio y formatos de reportes |
| `assets/escudo_colegio.png` | Escudo extraído del Word |

## Notas
- El **build del instalador** requiere Windows (Python 3.12 64-bit + Inno Setup 6). El desarrollo puede hacerse en cualquier SO.
- Probar el `Setup.exe` en una **PC limpia sin Python** antes de llevarlo a la directora (checklist en `docs/EMPAQUETADO.md §8`).
- Los archivos en `docs/referencia/` son punto de partida: no se han ejecutado.
- Decisiones por confirmar con el colegio (hay valores por defecto): `CLAUDE.md §9` (unidades por año, escala de notas, etc.).
