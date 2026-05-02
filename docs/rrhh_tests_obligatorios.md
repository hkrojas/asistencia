\# Tests obligatorios para planilla Perú



\## Regla general



Toda modificación en lógica de trabajadores, asistencia, incidencias, conceptos, cálculo de planilla, boletas o cierre debe incluir pruebas.



\## Tests mínimos



\### Trabajador



\- Crear trabajador activo con datos completos.

\- Bloquear trabajador activo sin documento.

\- Bloquear trabajador activo sin fecha de ingreso.

\- Bloquear trabajador activo sin régimen pensionario cuando corresponda.

\- Registrar historial al cambiar sueldo.

\- Registrar historial al cambiar cuenta bancaria.



\### Asistencia



\- Calcular tardanza.

\- Calcular falta injustificada.

\- Calcular licencia sin goce.

\- Calcular licencia con goce.

\- Calcular vacaciones.

\- Calcular horas extras solo si están aprobadas.

\- Auditar corrección manual de asistencia.



\### Preplanilla



\- Detectar trabajador sin cuenta bancaria.

\- Detectar horas extras pendientes.

\- Detectar faltas sin justificar.

\- Detectar descuentos inusuales.

\- Detectar variación fuerte contra mes anterior.

\- Impedir cierre con errores críticos.



\### Planilla



\- Calcular bruto.

\- Calcular descuentos.

\- Calcular aportes.

\- Calcular neto.

\- Comparar planilla actual contra planilla anterior.

\- Bloquear edición después del cierre.

\- Permitir reapertura solo con permiso especial.



\### Boletas



\- Generar boleta después del cierre.

\- No generar boleta si la planilla está en borrador.

\- Regenerar boleta dejando historial.

