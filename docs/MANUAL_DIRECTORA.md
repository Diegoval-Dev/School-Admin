# Manual de la directora

Sistema del Colegio "Julio González Celis" · Versión de desarrollo

Pasos numerados para usar el sistema sin conocimientos técnicos. Si algo no aparece como aquí, no lo cambies: avisa a soporte.

## 1. Abrir el sistema

1. Haz doble clic en el acceso directo **Sistema del Colegio** del escritorio.
2. Se abre el navegador en la página del sistema. Si no abre, escribe en el navegador la dirección que aparece en `C:\ColegioJGC\datos\puerto.txt` (por ejemplo `http://127.0.0.1:8000/`).
3. Para cerrar, usa el botón **Cerrar sistema** del menú. Al cerrar se hace un respaldo automático.

No hace falta internet. Los datos viven en la PC de la directora, en `C:\ColegioJGC`.

## 2. Primera vez: crear tu cuenta

1. La primera vez aparece la pantalla **Configuración inicial**.
2. Escribe tu nombre de usuario y una contraseña de al menos 8 caracteres (no uses solo números ni una palabra común).
3. Presiona **Crear cuenta**. Esta pantalla solo aparece mientras no exista ninguna cuenta.

## 3. Entrar

1. Escribe tu usuario y contraseña en la pantalla de entrada.
2. La sesión se cierra sola después de 2 horas sin usar el sistema. Vuelve a entrar si ocurre.

## 4. Crear la cuenta de la secretaria

1. En el menú izquierdo abre **Usuarios** y presiona **Agregar usuario**.
2. Escribe el nombre de usuario y una contraseña.
3. Marca **Miembro del personal** (sin esto no puede entrar).
4. En **Grupos**, elige **Secretaria**. Nunca la pongas en **Directora**.
5. Presiona **Guardar**.

La secretaria puede agregar, editar y ver datos. No puede borrar nada ni gestionar usuarios ni respaldos.

## 5. Registrar un estudiante

1. Menú **Estudiantes** → **Agregar estudiante**.
2. Escribe nombres, apellidos, fecha de nacimiento y género. El código se genera solo si lo dejas vacío.
3. Si el documento es CUI, escribe los 13 números.
4. Abajo, en **Responsables**, agrega padre, madre o tutor (una fila por cada uno).
5. En **Contactos** y **Direcciones** agrega teléfonos y direcciones.
6. En **Matrículas** agrega el ciclo, el grado y la jornada del año.
7. Presiona **Guardar**.

Un estudiante que se retira no se borra: cambia su **Estado** a *Retirado* o *Graduado*. Así sigue en los históricos.

Para ver el historial de cambios de un estudiante, abre su ficha y presiona **Historial**.

## 6. Registrar pagos

1. Menú **Pagos** → **Pagos por grado**.
2. Elige el ciclo, el grado y la jornada, y presiona **Mostrar**.
3. En la celda vacía (**+ Pagar**) escribe el monto, la fecha y el número de recibo, y presiona **Guardar pago**.
4. Celda verde = ya pagado. Celda gris = pendiente.
5. Para corregir un pago equivocado, abre el nombre del estudiante, presiona **Anular** en el pago y escribe el motivo. El pago no se borra: queda como anulado.
6. Para ver quién debe un mes, usa **Pendientes del mes**.

## 7. Pasar lista (asistencia)

1. Menú **Asistencia** → **Pasar lista**.
2. Elige ciclo, grado, jornada y mes, y presiona **Mostrar**.
3. Haz clic en la celda del estudiante y día para cambiarla: ✓ presente → ✗ ausente → E excusa → ✓.
4. Los fines de semana van sombreados. En la jornada de fin de semana solo aparecen sábados y domingos.
5. Las columnas P, A y E muestran los totales de cada estudiante.

Para imprimir o descargar a Excel, usa los botones de arriba de la tabla.

## 8. Registrar notas

1. Menú **Notas** → **Calificaciones**.
2. Elige ciclo, grado, materia y docente, y presiona **Mostrar**.
3. Escribe el punteo de cada unidad (de 0 a 100). Presiona **Enter** para bajar a la siguiente fila.
4. Lo que aparece en rojo está por debajo de 60.
5. Presiona **Guardar notas**. Si un punteo está mal, no se guarda ninguno: corrige el que aparece en el mensaje y vuelve a guardar.

## 9. Respaldos (muy importante)

El sistema hace respaldos automáticos al abrir, al cerrar y cada 2 horas. Además:

1. Una vez por semana, menú **Respaldos** → **Respaldar ahora**.
2. Copia el respaldo a una USB: escribe en **Ruta secundaria** la carpeta de la USB (por ejemplo `E:\Respaldos Colegio`) y presiona **Guardar ruta**. Cuando la USB esté conectada, cada respaldo se copia allí.
3. Si el sistema muestra un aviso de **Copia tu respaldo a la USB**, haz la copia ese mismo día.
4. Para tener una copia legible, presiona **Exportar todo a Excel**.
5. Después de copiar, desconecta la USB y guárdala en un lugar seguro.

### Restaurar un respaldo

Hazlo solo si el sistema está cerrado. Pide ayuda a soporte. Antes de restaurar, el sistema guarda una copia de lo que hay ahora.

## 10. Si algo falla

- **El sistema no abre:** cierra cualquier ventana del sistema, espera 1 minuto y vuelve a abrir el acceso directo.
- **Aparece "Ocurrió un error inesperado":** anota la hora y lo que estabas haciendo, y avisa a soporte. No apagues la PC a la fuerza.
- **Se cortó la luz mientras guardabas:** al volver a abrir, el sistema revisa la base de datos. Si hay un problema, te ofrecerá restaurar el último respaldo bueno.
- **Windows dice "protegió su PC" al instalar:** haz clic en **Más información** y luego **Ejecutar de todas formas**.
- **El antivirus bloquea el sistema:** agrega `C:\ColegioJGC` como excepción.
- **Pusiste un dato equivocado:** corrígelo en su ficha. Queda guardado el valor anterior en el historial.
