import calendar
from datetime import date

from django.core.exceptions import ValidationError

from colegio.models import Asistencia, EstadoAsistencia, Jornada, Matricula

DIAS_FIN_DE_SEMANA = (5, 6)
SIGUIENTE_ESTADO = {
    EstadoAsistencia.PRESENTE: EstadoAsistencia.AUSENTE,
    EstadoAsistencia.AUSENTE: EstadoAsistencia.EXCUSA,
    EstadoAsistencia.EXCUSA: EstadoAsistencia.SIN_REGISTRO,
    EstadoAsistencia.SIN_REGISTRO: EstadoAsistencia.PRESENTE,
}
ESTADOS_CONTABLES = (EstadoAsistencia.PRESENTE, EstadoAsistencia.AUSENTE, EstadoAsistencia.EXCUSA)
MENSAJE_MATRICULA_INACTIVA = "Solo se puede pasar lista a estudiantes con matrícula activa."


def es_fin_de_semana(fecha: date) -> bool:
    return fecha.weekday() in DIAS_FIN_DE_SEMANA


def dias_del_mes(anio: int, mes: int, jornada: str) -> list[date]:
    total_dias = calendar.monthrange(anio, mes)[1]
    dias = [date(anio, mes, dia) for dia in range(1, total_dias + 1)]
    if jornada == Jornada.FIN_SEMANA:
        return [dia for dia in dias if es_fin_de_semana(dia)]
    return dias


def ciclar_asistencia(matricula: Matricula, fecha: date) -> Asistencia:
    if not matricula.activa:
        raise ValidationError(MENSAJE_MATRICULA_INACTIVA)
    asistencia, creada = Asistencia.objects.get_or_create(
        matricula=matricula, fecha=fecha, defaults={"estado": EstadoAsistencia.PRESENTE}
    )
    if not creada:
        asistencia.estado = SIGUIENTE_ESTADO[asistencia.estado]
        asistencia.save()
    return asistencia


def filas_de_asistencia(matriculas, dias: list[date]) -> list[dict]:
    estados = {
        (asistencia.matricula_id, asistencia.fecha): asistencia.estado
        for asistencia in Asistencia.objects.filter(matricula__in=matriculas, fecha__in=dias)
    }
    return [_fila_de_asistencia(matricula, dias, estados) for matricula in matriculas]


def _fila_de_asistencia(matricula: Matricula, dias: list[date], estados: dict) -> dict:
    celdas = [(dia, estados.get((matricula.pk, dia))) for dia in dias]
    valores = [estado for _, estado in celdas if estado in ESTADOS_CONTABLES]
    return {
        "matricula": matricula,
        "celdas": celdas,
        "presentes": valores.count(EstadoAsistencia.PRESENTE),
        "ausentes": valores.count(EstadoAsistencia.AUSENTE),
        "excusas": valores.count(EstadoAsistencia.EXCUSA),
    }
