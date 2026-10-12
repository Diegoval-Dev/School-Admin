# Campos originales (lista del colegio) y formatos de reportes

Fuente: `Datos_para_base_de_datos_para_Manuel.docx`. Se conserva como referencia de lo que el colegio pidió. El diseño normalizado está en `MODELOS.md`.

## Estudiantes
Código personal · Primer apellido · Segundo apellido · Primer nombre · Segundo nombre · Tercer nombre · Fecha de nacimiento (y edad) · Género (Masculino/Femenino) · Nacionalidad (Guatemalteco/Extranjero) · Documento de identificación (CUI/Pasaporte) · No. de documento · Grado (1ro, 2do, 3ro Básico) · Ciclo (año) · Jornada (Plan Diario / Fin de semana)
- **Padre / Madre / Tutor y/o encargado:** nombre, nacionalidad, documento de identificación, no. de documento.
- **Direcciones físicas** (#1–#3), **Números de contacto** (#1–#3) cada uno con nombre del responsable.

## Docentes / Administrativo
Código docente/administración · nombres y apellidos (igual que estudiantes) · Fecha de nacimiento (y edad) · Género · Nacionalidad · Documento · No. de documento · Ciclo (año) · **Cursos #1–#8** (nombre de la materia + grado) · Dirección física #1 · Número de contacto #1 y #2

## Materias
Código materia · Nombre de la materia · Grado

## Mensualidades
Código personal · nombres y apellidos · Grado · Ciclo · Jornada · **Inscripción** · **Enero a Octubre** — cada uno con *Cantidad* y *Fecha de pago*.

---

## Formatos de reporte (todos con el escudo `assets/escudo_colegio.png`)

Encabezado común:
```
[escudo]  Colegio Mixto Presbítero "Julio González Celis"
Jornada: ______   Ciclo: ______   Grado: ______
```

### 1. Calificaciones
- Título: **Calificaciones**
- Datos: `Docente:` · `Materia:` · `Fecha:`
- Tabla: **No.** · **Apellidos** · **Nombres** · columnas de unidades (1–4) · **TOTAL**
- Pie: `FIRMA: __________________________`

### 2. Asistencia
- Título: **Asistencia** · `MES:`
- Tabla: **No.** · **Apellidos** · **Nombres** · columnas de días **1 a 31** (solo los días del mes) · totales al final de la fila
- Carta **horizontal**. Fines de semana sombreados. Leyenda: ✓ presente · ✗ ausente · E excusa

### 3. Pagos
- Título: **Pagos**
- Tabla: **No.** · **Apellidos** · **Nombres** · **Enero · Febrero · Marzo · Abril · Mayo · Junio · Julio · Agosto · Septiembre · Octubre** (+ columna Inscripción al inicio)
- Celda pagada: monto y fecha (corto). Pendiente: vacía. En pantalla, verde/gris; en impresión, ✓ y monto.

### Reportes adicionales (Fase 6)
Listado de estudiantes por grado/jornada · ficha imprimible del estudiante (datos, responsables, contactos) · estado de cuenta del estudiante · pendientes de pago del mes · estudiantes retirados/graduados.

## Notas de diseño de las planillas
- Numeración (**No.**) correlativa por orden alfabético de apellidos.
- Todos los reportes: botón **Imprimir** (Carta, márgenes 1.5 cm) y **Exportar a Excel** (openpyxl) con el mismo contenido.
- Después de la tabla de calificaciones/asistencia deben quedar filas vacías hasta completar la hoja si hay pocos estudiantes (para que se vea como la planilla de papel) — opcional.
