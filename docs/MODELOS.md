# Modelo de datos

Código de referencia: `docs/referencia/models_referencia.py`. Este documento explica **por qué** está así.

## Diagrama

```
CicloEscolar ──┬── Matricula ──┬── Pago (concepto: Inscripción, Ene…Oct)
               │       │       ├── Asistencia (fecha, P/A/E)
Estudiante ────┘       │       └── Nota (materia, unidad, punteo)
 ├─ Responsable (padre/madre/tutor)        ▲
 ├─ Contacto (teléfono + nombre)           │
 └─ Direccion                           Materia ◄── Asignacion ──► Docente, CicloEscolar
```

## Tablas

| Modelo | Reemplaza en la lista original | Notas |
|---|---|---|
| **Estudiante** | Datos personales del estudiante | Un registro de por vida. `estado`: Activo/Retirado/Graduado → así se distinguen actuales y antiguos. |
| **Responsable** | Nombre de Padre / Madre / Tutor y sus documentos | Una fila por relación (máx. 1 padre, 1 madre, 1 tutor por estudiante). |
| **Contacto** | Número de contacto #1..#3 + responsable | Cantidad ilimitada (inline en el admin). |
| **Direccion** | Dirección física #1..#3 | Cantidad ilimitada. |
| **Docente** | Docentes/Administrativo | Campo `tipo` distingue docente de administrativo. |
| **Asignacion** | Curso #1..#8 | Docente + materia + ciclo. Sin límite de 8. |
| **Materia** | Materias | `grado` incluido; la misma materia en otro grado es otro registro. |
| **CicloEscolar** | Ciclo / Año | Un registro por año; uno marcado como "actual". |
| **Matricula** | Grado, Ciclo, Jornada del estudiante | Estudiante × ciclo. Aquí vive el historial académico. |
| **Pago** | Mensualidades (Inscripción, Enero…Octubre) | Una fila por pago; se **anula**, no se borra. |
| **Asistencia** | Planilla de asistencia | Una fila por matrícula y día. |
| **Nota** | Planilla de calificaciones | Una fila por matrícula, materia y unidad. |

## Decisiones importantes

1. **Edad no se guarda** (se calcula desde `fecha_nacimiento`), para que nunca quede desactualizada.
2. **Matrícula por año:** un estudiante que pasa de 1ro a 2do no se duplica; se crea otra matrícula. Los antiguos siguen consultables con todo su historial (pagos, notas, asistencia).
3. **Pagos = filas, no columnas.** El reporte "estudiantes × meses" se genera dinámicamente. Agregar un mes en el futuro es un valor más en el enum.
4. **Nada se borra.** `on_delete=PROTECT`, estados y anulaciones. Los errores se corrigen editando (y queda en el historial de cambios).
5. **Documento único:** si se ingresó CUI/pasaporte, no puede repetirse entre estudiantes (hermanos comparten el de los padres, no el propio). Se permite vacío porque algunos datos llegan incompletos.
6. **Asistencia por día** (no por materia): así es la planilla original.
7. **Notas:** una sola columna `punteo` por unidad (el total). Si luego quieren desglosar actividades (zona, examen), se agrega un modelo `Actividad` sin romper nada.
8. **Auditoría** (`simple_history`) en Estudiante, Responsable, Docente, Matrícula, Pago y Nota: quién y cuándo cambió cada dato, con valores anteriores.

## Validaciones

- CUI: exactamente 13 dígitos (se normalizan espacios). Pasaporte: libre.
- Una matrícula por estudiante y ciclo.
- Nota dentro de `NOTA_MIN..NOTA_MAX`, unidad entre 1 y `UNIDADES_POR_CICLO`, y la materia debe ser del mismo grado que la matrícula.
- Un solo pago vigente por matrícula + concepto.
- Anular un pago exige motivo.

## Códigos automáticos

- Estudiante (si se deja vacío): `AAAA-NNNN` → año de ingreso + secuencia (ej. `2026-0001`). Debe ser a prueba de colisiones (usar transacción y buscar el máximo existente).
- Docente: `D-NNN`.
- Materia: se ingresa a mano (ej. `MAT-1B`).
