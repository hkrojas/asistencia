\# Flujo de cierre de planilla - RRHH Perú



\## 1. Objetivo



Definir el flujo operativo que debe seguir RRHH para cerrar una planilla mensual de forma controlada, auditable y preparada para obligaciones laborales peruanas.



El cierre de planilla no debe ser un botón aislado. Debe ser un proceso con etapas, validaciones, aprobaciones y bloqueo posterior.



\## 2. Actores



\### RRHH



Responsable de revisar trabajadores, contratos, asistencia, incidencias, conceptos y preplanilla.



\### Jefe de área



Responsable de validar incidencias operativas como horas extras, permisos, faltas justificadas o asistencia corregida.



\### Finanzas



Responsable de revisar netos a pagar, cuentas bancarias, adelantos, préstamos, pagos y constancias.



\### Administrador



Responsable de configuración, permisos, conceptos y reapertura excepcional.



\### Trabajador



Consulta boletas, solicitudes y datos personales cuando exista portal de trabajador.



\## 3. Estados de planilla



La planilla debe manejar estos estados:



1\. Borrador.

2\. En revisión.

3\. Observada.

4\. Validada por RRHH.

5\. Validada por Finanzas.

6\. Cerrada.

7\. Pagada.

8\. Reabierta.

9\. Anulada.



\## 4. Flujo general



\### Paso 1: Crear periodo de planilla



RRHH crea o abre el periodo.



Datos requeridos:



\- Empresa.

\- Periodo.

\- Fecha de inicio.

\- Fecha de fin.

\- Tipo de planilla.

\- Moneda.

\- Responsable RRHH.

\- Estado inicial: Borrador.



Validaciones:



\- No debe existir otra planilla abierta del mismo tipo y periodo.

\- No debe existir una planilla cerrada duplicada para el mismo periodo.

\- El periodo debe tener fechas válidas.



\### Paso 2: Sincronizar trabajadores activos



El sistema debe cargar trabajadores que correspondan al periodo.



Debe incluir:



\- Trabajadores activos antes o durante el periodo.

\- Trabajadores ingresados durante el periodo.

\- Trabajadores cesados durante el periodo, si corresponde pago proporcional o liquidación.

\- Trabajadores suspendidos o en licencia, si corresponde.



Validaciones:



\- Trabajador sin fecha de ingreso.

\- Trabajador activo sin sueldo.

\- Trabajador activo sin régimen pensionario.

\- Trabajador activo sin datos bancarios.

\- Trabajador activo sin contrato vigente.

\- Trabajador cesado sin fecha de cese.

\- Trabajador con datos laborales incompletos.



Resultado:



\- Lista preliminar de trabajadores incluidos.

\- Lista de trabajadores observados.

\- Lista de trabajadores excluidos y motivo.



\### Paso 3: Importar o consolidar asistencia



El sistema consolida:



\- Marcaciones.

\- Horarios.

\- Tardanzas.

\- Faltas.

\- Salidas anticipadas.

\- Horas extras.

\- Feriados.

\- Descansos médicos.

\- Licencias.

\- Permisos.

\- Vacaciones.



Fuentes posibles:



\- Registro manual.

\- Importación Excel.

\- Reloj biométrico.

\- Solicitudes aprobadas.

\- Correcciones autorizadas.



Validaciones:



\- Marcaciones incompletas.

\- Días sin asistencia ni justificación.

\- Horas extras sin aprobación.

\- Vacaciones no aprobadas.

\- Licencias sin documento.

\- Descanso médico sin archivo.

\- Correcciones manuales sin motivo.

\- Horario no asignado.



Resultado:



\- Resumen de asistencia por trabajador.

\- Incidencias generadas automáticamente.

\- Incidencias pendientes de aprobación.



\### Paso 4: Revisar incidencias



RRHH revisa todas las incidencias del periodo.



Tipos de incidencia:



\- Tardanza.

\- Falta injustificada.

\- Falta justificada.

\- Licencia con goce.

\- Licencia sin goce.

\- Descanso médico.

\- Vacaciones.

\- Horas extras.

\- Bono.

\- Comisión.

\- Adelanto.

\- Préstamo.

\- Descuento.

\- Reintegro.

\- Suspensión.

\- Cese.



Estados:



\- Registrada.

\- Pendiente.

\- Aprobada.

\- Rechazada.

\- Anulada.



Reglas:



\- Solo incidencias aprobadas deben afectar la planilla.

\- Horas extras no aprobadas no deben pagarse.

\- Faltas no justificadas deben quedar visibles en preplanilla.

\- Toda incidencia manual debe tener motivo.

\- Toda incidencia sensible debe dejar auditoría.



\### Paso 5: Generar preplanilla



La preplanilla es una simulación revisable antes del cierre.



Debe mostrar por trabajador:



\- Sueldo base.

\- Días del periodo.

\- Días trabajados.

\- Días no trabajados.

\- Horas ordinarias.

\- Horas extras aprobadas.

\- Ingresos.

\- Descuentos.

\- Aportes del trabajador.

\- Aportes del empleador.

\- Neto estimado.

\- Observaciones.

\- Alertas.



Debe mostrar totales:



\- Total bruto.

\- Total descuentos.

\- Total aportes trabajador.

\- Total aportes empleador.

\- Total neto.

\- Costo empresa estimado.

\- Variación contra periodo anterior.



\### Paso 6: Ejecutar validaciones de pre-cierre



Antes de permitir cierre, el sistema debe ejecutar validaciones.



\#### Errores críticos bloqueantes



\- Trabajador activo sin sueldo.

\- Trabajador activo sin régimen pensionario.

\- Trabajador activo sin fecha de ingreso.

\- Trabajador incluido sin datos mínimos.

\- Trabajador con neto negativo.

\- Trabajador sin cuenta bancaria, si el pago será bancario.

\- Planilla sin trabajadores.

\- Concepto de planilla sin configuración.

\- Fórmula de cálculo inválida.

\- Horas extras aprobadas sin base de cálculo.

\- Reapertura pendiente de una planilla anterior.



\#### Advertencias no bloqueantes



\- Contrato por vencer.

\- Variación salarial mayor al umbral configurado.

\- Neto muy distinto al mes anterior.

\- Muchas tardanzas en el periodo.

\- Muchas faltas justificadas.

\- Trabajador nuevo sin documento adjunto.

\- Trabajador cesado pendiente de liquidación.

\- Cuenta bancaria no validada.



\### Paso 7: Comparar contra mes anterior



El sistema debe permitir comparar la planilla actual contra la anterior.



Debe mostrar:



\- Variación total de planilla.

\- Variación por área.

\- Variación por trabajador.

\- Nuevos ingresos.

\- Ceses.

\- Aumentos salariales.

\- Nuevos descuentos.

\- Nuevos bonos.

\- Horas extras adicionales.

\- Incidencias relevantes.



Ejemplo esperado:



Planilla abril vs marzo:

\- Total neto: +S/ 4,500.

\- Causa:

&#x20; - 2 nuevos trabajadores.

&#x20; - 1 aumento salarial.

&#x20; - 18 horas extras adicionales.

&#x20; - 1 trabajador cesado.

&#x20; - 3 descuentos por préstamo.



\### Paso 8: Validación de RRHH



RRHH revisa la preplanilla.



Acciones posibles:



\- Aprobar preplanilla.

\- Observar trabajador.

\- Excluir trabajador con motivo.

\- Solicitar corrección.

\- Regenerar cálculo.

\- Enviar a Finanzas.



Reglas:



\- La aprobación de RRHH debe registrar usuario, fecha y hora.

\- Si se modifica una incidencia después de aprobar, la aprobación debe invalidarse.

\- Si se modifica un sueldo después de aprobar, la aprobación debe invalidarse.



\### Paso 9: Validación de Finanzas



Finanzas revisa:



\- Netos a pagar.

\- Cuentas bancarias.

\- Adelantos.

\- Préstamos.

\- Descuentos.

\- Variaciones relevantes.

\- Total de pago.

\- Reportes bancarios.



Acciones posibles:



\- Aprobar pago.

\- Observar pago.

\- Solicitar corrección.

\- Descargar resumen.

\- Generar archivo bancario, si aplica.



Reglas:



\- Si Finanzas observa la planilla, vuelve a estado Observada.

\- Si Finanzas aprueba, queda lista para cierre.

\- La aprobación debe dejar auditoría.



\### Paso 10: Cerrar planilla



Solo se puede cerrar si:



\- No hay errores críticos.

\- RRHH aprobó.

\- Finanzas aprobó, si aplica.

\- No existen incidencias pendientes críticas.

\- No existen cálculos inválidos.

\- El usuario tiene permiso de cierre.



Al cerrar:



\- Se congelan los montos.

\- Se genera snapshot de cálculo.

\- Se bloquea edición directa.

\- Se registra auditoría.

\- Se habilita generación de boletas definitivas.

\- Se habilita preparación de pagos.



Datos de auditoría:



\- Usuario que cerró.

\- Fecha y hora.

\- Periodo.

\- Total bruto.

\- Total descuentos.

\- Total aportes.

\- Total neto.

\- Número de trabajadores.

\- Hash o identificador de cierre, si se implementa.



\### Paso 11: Generar boletas



Después del cierre, RRHH puede generar boletas.



Opciones:



\- Generar boleta individual.

\- Generar boletas masivas.

\- Descargar PDF.

\- Enviar por correo.

\- Registrar entrega.

\- Regenerar boleta con nueva versión si hubo reapertura.



Reglas:



\- No generar boletas definitivas desde planilla en borrador.

\- Toda boleta debe estar asociada a una planilla cerrada.

\- Si la planilla se reabre y cambia, las boletas anteriores deben quedar como reemplazadas o anuladas, no eliminarse.



\### Paso 12: Preparar pagos



Finanzas prepara el pago.



Debe poder:



\- Ver total a pagar.

\- Ver trabajadores incluidos.

\- Filtrar por banco.

\- Validar cuentas.

\- Exportar resumen.

\- Generar archivo bancario, si se implementa.

\- Adjuntar constancia.

\- Marcar como pagado.



Estados de pago:



\- Pendiente.

\- Preparado.

\- Enviado al banco.

\- Observado.

\- Pagado.

\- Parcialmente pagado.



\### Paso 13: Marcar planilla como pagada



La planilla puede pasar a pagada cuando:



\- Existe fecha de pago.

\- Existe responsable.

\- Existe monto pagado.

\- Existe constancia o referencia, si aplica.

\- No hay pagos críticos pendientes.



Resultado:



\- Planilla cerrada y pagada.

\- Boletas disponibles.

\- Reportes disponibles.

\- Auditoría completa.



\## 5. Reapertura de planilla



La reapertura debe ser excepcional.



Solo puede realizarla un usuario autorizado.



Motivos posibles:



\- Error de cálculo.

\- Incidencia omitida.

\- Trabajador omitido.

\- Descuento incorrecto.

\- Bono incorrecto.

\- Corrección solicitada por Finanzas.

\- Corrección documentaria.



Reglas:



\- Requiere motivo obligatorio.

\- Requiere auditoría.

\- Debe conservar versión anterior.

\- Debe invalidar boletas generadas si cambian montos.

\- Debe exigir nuevo cierre.

\- Debe generar nueva versión de planilla.



No se debe editar una planilla cerrada sin cambiar su estado a reabierta.



\## 6. Anulación



Una planilla solo debe anularse en casos excepcionales.



Debe registrar:



\- Motivo.

\- Usuario.

\- Fecha.

\- Estado anterior.

\- Documentos relacionados.

\- Impacto en boletas.

\- Impacto en pagos.



\## 7. Pantallas recomendadas



\### Dashboard de planilla



Debe mostrar:



\- Periodo actual.

\- Estado de planilla.

\- Trabajadores incluidos.

\- Errores críticos.

\- Advertencias.

\- Total estimado.

\- Variación contra mes anterior.

\- Incidencias pendientes.

\- Contratos por vencer.

\- Botón: revisar preplanilla.



\### Preplanilla



Debe mostrar:



\- Tabla por trabajador.

\- Filtros por área.

\- Filtros por estado.

\- Alertas.

\- Ingresos.

\- Descuentos.

\- Neto.

\- Acciones por trabajador.

\- Botón: recalcular.

\- Botón: enviar a aprobación.



\### Detalle de trabajador en planilla



Debe mostrar:



\- Datos laborales.

\- Sueldo.

\- Asistencia.

\- Incidencias.

\- Ingresos.

\- Descuentos.

\- Aportes.

\- Neto.

\- Comparación contra mes anterior.

\- Historial de cambios.



\### Cierre



Debe mostrar:



\- Resumen final.

\- Checklist de validación.

\- Aprobaciones.

\- Advertencias.

\- Confirmación fuerte.

\- Campo de comentario.

\- Botón de cerrar planilla.



\## 8. Tests obligatorios del flujo



Debe existir prueba para:



\- Crear planilla en borrador.

\- Cargar trabajadores activos.

\- Excluir trabajadores cesados fuera del periodo.

\- Incluir trabajador ingresado durante el periodo.

\- Detectar trabajador sin sueldo.

\- Detectar trabajador sin régimen pensionario.

\- Detectar trabajador sin cuenta bancaria.

\- Generar preplanilla.

\- Calcular neto.

\- Bloquear cierre con errores críticos.

\- Permitir cierre sin errores críticos.

\- Bloquear edición después del cierre.

\- Reabrir con permiso.

\- Impedir reapertura sin permiso.

\- Invalidar boletas después de reapertura con cambios.

\- Generar boleta solo desde planilla cerrada.

\- Marcar planilla como pagada.

