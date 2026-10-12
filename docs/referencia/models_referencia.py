"""
REFERENCIA de colegio/models.py  —  punto de partida, NO ejecutado todavía.
Claude Code: impleméntalo, pruébalo, corrige lo que haga falta y genera las migraciones.

Decisiones clave (ver docs/MODELOS.md):
- Un solo registro de Estudiante para toda la vida; cada año es una Matricula (grado + jornada).
- Edad nunca se guarda: se calcula.
- Pagos = una fila por concepto (Inscripción, Ene..Oct), se ANULAN, no se borran.
- Todo con on_delete=PROTECT y auditoría con simple_history.
"""
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from simple_history.models import HistoricalRecords

NOTA_MIN = Decimal(str(getattr(settings, "NOTA_MIN", 0)))
NOTA_MAX = Decimal(str(getattr(settings, "NOTA_MAX", 100)))
UNIDADES_POR_CICLO = getattr(settings, "UNIDADES_POR_CICLO", 4)


# ───────────────────────── Catálogos ─────────────────────────
class Genero(models.TextChoices):
    MASCULINO = "M", "Masculino"
    FEMENINO = "F", "Femenino"


class Nacionalidad(models.TextChoices):
    GUATEMALTECO = "GT", "Guatemalteco"
    EXTRANJERO = "EX", "Extranjero"


class TipoDocumento(models.TextChoices):
    CUI = "CUI", "CUI"
    PASAPORTE = "PAS", "Pasaporte"


class Grado(models.TextChoices):
    PRIMERO = "1B", "1ro Básico"
    SEGUNDO = "2B", "2do Básico"
    TERCERO = "3B", "3ro Básico"


class Jornada(models.TextChoices):
    DIARIO = "D", "Plan Diario"
    FIN_SEMANA = "FS", "Fin de semana"


class EstadoEstudiante(models.TextChoices):
    ACTIVO = "A", "Activo"
    RETIRADO = "R", "Retirado"
    GRADUADO = "G", "Graduado"


class Relacion(models.TextChoices):
    PADRE = "PA", "Padre"
    MADRE = "MA", "Madre"
    TUTOR = "TU", "Tutor / Encargado"


class Concepto(models.TextChoices):
    """Orden de las columnas en el reporte de pagos."""
    INSCRIPCION = "00", "Inscripción"
    ENERO = "01", "Enero"
    FEBRERO = "02", "Febrero"
    MARZO = "03", "Marzo"
    ABRIL = "04", "Abril"
    MAYO = "05", "Mayo"
    JUNIO = "06", "Junio"
    JULIO = "07", "Julio"
    AGOSTO = "08", "Agosto"
    SEPTIEMBRE = "09", "Septiembre"
    OCTUBRE = "10", "Octubre"


class EstadoAsistencia(models.TextChoices):
    PRESENTE = "P", "Presente"
    AUSENTE = "A", "Ausente"
    EXCUSA = "E", "Excusa"


# ───────────────────────── Base de personas ─────────────────────────
class Persona(models.Model):
    primer_apellido = models.CharField("Primer apellido", max_length=60)
    segundo_apellido = models.CharField("Segundo apellido", max_length=60, blank=True)
    primer_nombre = models.CharField("Primer nombre", max_length=60)
    segundo_nombre = models.CharField("Segundo nombre", max_length=60, blank=True)
    tercer_nombre = models.CharField("Tercer nombre", max_length=60, blank=True)
    fecha_nacimiento = models.DateField("Fecha de nacimiento", null=True, blank=True)
    genero = models.CharField("Género", max_length=1, choices=Genero.choices)
    nacionalidad = models.CharField(
        "Nacionalidad", max_length=2, choices=Nacionalidad.choices, default=Nacionalidad.GUATEMALTECO
    )
    tipo_documento = models.CharField(
        "Documento de identificación", max_length=3, choices=TipoDocumento.choices, default=TipoDocumento.CUI
    )
    numero_documento = models.CharField("No. de documento", max_length=30, blank=True)

    class Meta:
        abstract = True

    @property
    def apellidos(self) -> str:
        return " ".join(p for p in (self.primer_apellido, self.segundo_apellido) if p)

    @property
    def nombres(self) -> str:
        return " ".join(p for p in (self.primer_nombre, self.segundo_nombre, self.tercer_nombre) if p)

    @property
    def nombre_completo(self) -> str:
        return f"{self.apellidos}, {self.nombres}"

    @property
    def edad(self):
        if not self.fecha_nacimiento:
            return None
        hoy = date.today()
        n = self.fecha_nacimiento
        return hoy.year - n.year - ((hoy.month, hoy.day) < (n.month, n.day))

    def clean(self):
        super().clean()
        if self.tipo_documento == TipoDocumento.CUI and self.numero_documento:
            solo = self.numero_documento.replace(" ", "")
            if not (solo.isdigit() and len(solo) == 13):
                raise ValidationError({"numero_documento": "El CUI debe tener 13 dígitos."})
            self.numero_documento = solo

    def __str__(self):
        return self.nombre_completo


class Auditable(models.Model):
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ───────────────────────── Ciclo y materias ─────────────────────────
class CicloEscolar(Auditable):
    anio = models.PositiveSmallIntegerField("Año", unique=True)
    activo = models.BooleanField("Ciclo actual", default=False)

    class Meta:
        verbose_name = "ciclo escolar"
        verbose_name_plural = "ciclos escolares"
        ordering = ["-anio"]

    def __str__(self):
        return str(self.anio)


class Materia(Auditable):
    codigo = models.CharField("Código", max_length=20, unique=True)
    nombre = models.CharField("Nombre de la materia", max_length=100)
    grado = models.CharField("Grado", max_length=2, choices=Grado.choices)

    class Meta:
        ordering = ["grado", "nombre"]
        constraints = [models.UniqueConstraint(fields=["nombre", "grado"], name="materia_unica_por_grado")]

    def __str__(self):
        return f"{self.nombre} ({self.get_grado_display()})"


# ───────────────────────── Estudiantes ─────────────────────────
class Estudiante(Persona, Auditable):
    codigo = models.CharField("Código personal", max_length=20, unique=True, blank=True,
                              help_text="Si se deja vacío, se genera automáticamente.")
    estado = models.CharField("Estado", max_length=1, choices=EstadoEstudiante.choices,
                              default=EstadoEstudiante.ACTIVO)
    observaciones = models.TextField("Observaciones", blank=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["primer_apellido", "segundo_apellido", "primer_nombre"]
        constraints = [
            # Un mismo documento no puede pertenecer a dos estudiantes (si se ingresó).
            models.UniqueConstraint(
                fields=["tipo_documento", "numero_documento"],
                condition=~Q(numero_documento=""),
                name="estudiante_documento_unico",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.codigo:
            from .services.codigos import siguiente_codigo_estudiante  # implementar en Fase 1
            self.codigo = siguiente_codigo_estudiante()
        super().save(*args, **kwargs)


class Responsable(Auditable):
    """Padre, madre o tutor. Un registro por relación."""
    estudiante = models.ForeignKey(Estudiante, on_delete=models.PROTECT, related_name="responsables")
    relacion = models.CharField("Relación", max_length=2, choices=Relacion.choices)
    nombre_completo = models.CharField("Nombre completo", max_length=200)
    nacionalidad = models.CharField("Nacionalidad", max_length=2, choices=Nacionalidad.choices,
                                    default=Nacionalidad.GUATEMALTECO)
    tipo_documento = models.CharField("Documento", max_length=3, choices=TipoDocumento.choices,
                                      default=TipoDocumento.CUI)
    numero_documento = models.CharField("No. de documento", max_length=30, blank=True)
    history = HistoricalRecords()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["estudiante", "relacion"], name="una_relacion_por_estudiante")]

    def __str__(self):
        return f"{self.get_relacion_display()}: {self.nombre_completo}"


class Contacto(Auditable):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.PROTECT, related_name="contactos")
    telefono = models.CharField("Teléfono", max_length=20)
    nombre_responsable = models.CharField("Nombre del responsable", max_length=200, blank=True)

    def __str__(self):
        return f"{self.telefono} ({self.nombre_responsable})"


class Direccion(Auditable):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.PROTECT, related_name="direcciones")
    direccion = models.CharField("Dirección física", max_length=255)

    class Meta:
        verbose_name = "dirección"
        verbose_name_plural = "direcciones"

    def __str__(self):
        return self.direccion


# ───────────────────────── Docentes / Administrativos ─────────────────────────
class Docente(Persona, Auditable):
    class Tipo(models.TextChoices):
        DOCENTE = "D", "Docente"
        ADMINISTRATIVO = "A", "Administrativo"

    codigo = models.CharField("Código", max_length=20, unique=True, blank=True)
    tipo = models.CharField("Tipo", max_length=1, choices=Tipo.choices, default=Tipo.DOCENTE)
    activo = models.BooleanField("Activo", default=True)
    telefono_1 = models.CharField("Teléfono 1", max_length=20, blank=True)
    telefono_2 = models.CharField("Teléfono 2", max_length=20, blank=True)
    direccion = models.CharField("Dirección física", max_length=255, blank=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "docente / administrativo"
        verbose_name_plural = "docentes y administrativos"
        ordering = ["primer_apellido", "primer_nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["tipo_documento", "numero_documento"],
                condition=~Q(numero_documento=""),
                name="docente_documento_unico",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.codigo:
            from .services.codigos import siguiente_codigo_docente
            self.codigo = siguiente_codigo_docente()
        super().save(*args, **kwargs)


class Asignacion(Auditable):
    """Qué docente da qué materia en qué ciclo. Reemplaza 'Curso #1..#8'."""
    docente = models.ForeignKey(Docente, on_delete=models.PROTECT, related_name="asignaciones")
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT, related_name="asignaciones")
    ciclo = models.ForeignKey(CicloEscolar, on_delete=models.PROTECT, related_name="asignaciones")

    class Meta:
        verbose_name = "curso asignado"
        verbose_name_plural = "cursos asignados"
        constraints = [models.UniqueConstraint(fields=["docente", "materia", "ciclo"], name="asignacion_unica")]

    def __str__(self):
        return f"{self.docente} → {self.materia} ({self.ciclo})"


# ───────────────────────── Matrícula (estudiante × año) ─────────────────────────
class Matricula(Auditable):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.PROTECT, related_name="matriculas")
    ciclo = models.ForeignKey(CicloEscolar, on_delete=models.PROTECT, related_name="matriculas")
    grado = models.CharField("Grado", max_length=2, choices=Grado.choices)
    jornada = models.CharField("Jornada", max_length=2, choices=Jornada.choices, default=Jornada.DIARIO)
    activa = models.BooleanField("Activa", default=True, help_text="Desmarcar si se retira durante el año.")
    history = HistoricalRecords()

    class Meta:
        ordering = ["-ciclo__anio", "grado", "estudiante__primer_apellido"]
        constraints = [models.UniqueConstraint(fields=["estudiante", "ciclo"], name="una_matricula_por_ciclo")]

    def __str__(self):
        return f"{self.estudiante.nombre_completo} — {self.ciclo} {self.get_grado_display()}"


# ───────────────────────── Pagos ─────────────────────────
class Pago(Auditable):
    matricula = models.ForeignKey(Matricula, on_delete=models.PROTECT, related_name="pagos")
    concepto = models.CharField("Concepto", max_length=2, choices=Concepto.choices)
    monto = models.DecimalField("Monto (Q)", max_digits=8, decimal_places=2,
                                validators=[MinValueValidator(Decimal("0.01"))])
    fecha_pago = models.DateField("Fecha de pago")
    numero_recibo = models.CharField("No. de recibo", max_length=30, blank=True)
    observaciones = models.CharField(max_length=255, blank=True)
    anulado = models.BooleanField("Anulado", default=False)
    motivo_anulacion = models.CharField("Motivo de anulación", max_length=255, blank=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["matricula", "concepto"]
        constraints = [
            # Solo un pago VIGENTE por matrícula + concepto. Los anulados pueden repetirse.
            models.UniqueConstraint(
                fields=["matricula", "concepto"], condition=Q(anulado=False), name="pago_vigente_unico"
            )
        ]

    def clean(self):
        super().clean()
        if self.anulado and not self.motivo_anulacion:
            raise ValidationError({"motivo_anulacion": "Indica el motivo de la anulación."})

    def __str__(self):
        return f"{self.matricula} · {self.get_concepto_display()} · Q{self.monto}"


# ───────────────────────── Asistencia ─────────────────────────
class Asistencia(Auditable):
    matricula = models.ForeignKey(Matricula, on_delete=models.PROTECT, related_name="asistencias")
    fecha = models.DateField()
    estado = models.CharField(max_length=1, choices=EstadoAsistencia.choices)

    class Meta:
        verbose_name_plural = "asistencias"
        constraints = [models.UniqueConstraint(fields=["matricula", "fecha"], name="una_asistencia_por_dia")]
        indexes = [models.Index(fields=["fecha"])]

    def __str__(self):
        return f"{self.matricula.estudiante} {self.fecha} {self.estado}"


# ───────────────────────── Notas ─────────────────────────
class Nota(Auditable):
    matricula = models.ForeignKey(Matricula, on_delete=models.PROTECT, related_name="notas")
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT, related_name="notas")
    unidad = models.PositiveSmallIntegerField("Unidad")
    punteo = models.DecimalField("Punteo", max_digits=5, decimal_places=2)
    history = HistoricalRecords()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["matricula", "materia", "unidad"], name="una_nota_por_unidad")]

    def clean(self):
        super().clean()
        if not (1 <= self.unidad <= UNIDADES_POR_CICLO):
            raise ValidationError({"unidad": f"La unidad debe estar entre 1 y {UNIDADES_POR_CICLO}."})
        if self.punteo is not None and not (NOTA_MIN <= self.punteo <= NOTA_MAX):
            raise ValidationError({"punteo": f"El punteo debe estar entre {NOTA_MIN} y {NOTA_MAX}."})
        if self.materia_id and self.matricula_id and self.materia.grado != self.matricula.grado:
            raise ValidationError({"materia": "La materia no corresponde al grado del estudiante."})

    def __str__(self):
        return f"{self.matricula.estudiante} · {self.materia.nombre} · U{self.unidad}: {self.punteo}"
