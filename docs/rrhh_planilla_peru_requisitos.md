\# Requisitos funcionales - Sistema RRHH y Planilla Perú



\## 1. Objetivo del módulo



Este sistema debe permitir que un usuario de RRHH pueda gestionar trabajadores, contratos, asistencia, incidencias, cálculo de planilla, boletas de pago, pagos, beneficios sociales, reportes y auditoría interna, considerando el contexto laboral peruano.



El sistema no debe ser solo un registro de trabajadores. Debe permitir cerrar una planilla mensual con validaciones, trazabilidad y preparación para obligaciones laborales y tributarias.



\## 2. Principio central



El flujo principal del sistema es:



Trabajador → Contrato → Asistencia → Incidencias → Preplanilla → Cálculo → Revisión → Cierre → Boletas → Pago → Reportes.



Si RRHH necesita volver a Excel para validar tardanzas, faltas, vacaciones, horas extras, descuentos o netos a pagar, el módulo se considera incompleto.



\## 3. Alcance normativo base



El sistema debe diseñarse considerando como referencia:



\- SUNAT - Planilla Electrónica.

\- T-Registro.

\- PLAME.

\- SUNAFIL.

\- Ministerio de Trabajo y Promoción del Empleo.

\- EsSalud.

\- AFP / ONP.

\- Normativa sobre beneficios sociales.

\- Normativa de seguridad y salud en el trabajo, cuando corresponda.



Toda regla laboral, tributaria o previsional debe estar documentada con:



\- Fuente.

\- Fecha de consulta.

\- Vigencia.

\- Supuesto aplicado.

\- Módulo afectado.

\- Tests asociados.



\## 4. Separación conceptual obligatoria



El sistema debe separar dos bloques:



\### 4.1 Información laboral estructural



Equivale funcionalmente al bloque tipo T-Registro.



Incluye:



\- Datos del empleador.

\- Datos del trabajador.

\- Datos laborales.

\- Datos de seguridad social.

\- Régimen pensionario.

\- Derechohabientes, si se implementa.

\- Fecha de alta.

\- Fecha de baja.

\- Modificaciones laborales.

\- Histórico del trabajador.



\### 4.2 Información mensual de pagos



Equivale funcionalmente al bloque tipo PLAME.



Incluye:



\- Remuneraciones del periodo.

\- Conceptos remunerativos.

\- Conceptos no remunerativos.

\- Descuentos.

\- Aportes del trabajador.

\- Aportes del empleador.

\- Días laborados.

\- Días no laborados.

\- Horas ordinarias.

\- Horas extras.

\- Bases de cálculo.

\- Neto a pagar.

\- Periodo tributario/laboral.



\## 5. Módulo de trabajadores



El sistema debe permitir registrar y mantener una ficha completa del trabajador.



\### Datos mínimos



\- Tipo de documento.

\- Número de documento.

\- Nombres y apellidos.

\- Fecha de nacimiento.

\- Dirección.

\- Teléfono.

\- Correo.

\- Estado civil, si aplica.

\- Nacionalidad, si aplica.

\- Contacto de emergencia.

\- Estado laboral: activo, cesado, suspendido, vacaciones, licencia.



\### Datos laborales



\- Fecha de ingreso.

\- Cargo.

\- Área.

\- Sede.

\- Centro de costo.

\- Tipo de trabajador.

\- Régimen laboral.

\- Jornada.

\- Modalidad: presencial, remoto, híbrido.

\- Tipo de contrato.

\- Fecha de inicio de contrato.

\- Fecha de fin de contrato, si aplica.

\- Periodo de prueba, si aplica.

\- Jefe directo.



\### Datos salariales



\- Sueldo básico.

\- Moneda.

\- Periodicidad.

\- Condición salarial.

\- Bonificaciones fijas.

\- Asignaciones.

\- Comisiones.

\- Historial salarial.



\### Datos previsionales y salud



\- Sistema pensionario: AFP u ONP.

\- AFP.

\- CUSPP, si aplica.

\- Tipo de comisión AFP, si aplica.

\- EsSalud u otro seguro permitido según régimen.

\- SCTR, si corresponde por actividad.

\- Seguro Vida Ley, si corresponde.



\### Datos bancarios



\- Banco.

\- Tipo de cuenta.

\- Número de cuenta.

\- CCI.

\- Titular.

\- Estado de validación.



\### Documentos



\- DNI o documento de identidad.

\- Contrato.

\- Adendas.

\- CV.

\- Certificados.

\- Descansos médicos.

\- Solicitudes aprobadas.

\- Documentos de cese.

\- Otros documentos laborales.



\## 6. Historial obligatorio



El sistema debe guardar historial de cambios sensibles.



Debe auditarse:



\- Cambio de sueldo.

\- Cambio de cargo.

\- Cambio de área.

\- Cambio de contrato.

\- Cambio de régimen pensionario.

\- Cambio de cuenta bancaria.

\- Cambio de estado laboral.

\- Registro de cese.

\- Modificación de fecha de ingreso.

\- Modificación de asistencia.

\- Registro manual de incidencias.

\- Aprobación de horas extras.

\- Cierre de planilla.

\- Reapertura de planilla.



Cada auditoría debe registrar:



\- Usuario.

\- Fecha y hora.

\- Valor anterior.

\- Valor nuevo.

\- Motivo.

\- Documento de respaldo, si aplica.



\## 7. Módulo de contratos



El sistema debe permitir:



\- Registrar contratos.

\- Renovar contratos.

\- Generar adendas.

\- Alertar contratos por vencer.

\- Registrar finalización.

\- Registrar motivo de cese.

\- Asociar documentos.

\- Mantener historial contractual.



\### Alertas mínimas



\- Contratos que vencen en 30 días.

\- Contratos vencidos.

\- Contratos sin documento adjunto.

\- Trabajadores activos sin contrato vigente.

\- Trabajadores cesados pendientes de liquidación.



\## 8. Módulo de asistencia



La asistencia debe alimentar la preplanilla y no quedarse como simple registro visual.



Debe permitir:



\- Registro de marcaciones.

\- Importación desde Excel.

\- Importación desde reloj biométrico, si aplica.

\- Horarios fijos.

\- Horarios rotativos.

\- Tardanzas.

\- Faltas.

\- Salidas anticipadas.

\- Horas extras.

\- Trabajo en feriados.

\- Descansos médicos.

\- Permisos.

\- Licencias con goce.

\- Licencias sin goce.

\- Vacaciones.

\- Marcaciones corregidas manualmente.



\### Regla



Toda corrección manual de asistencia debe dejar auditoría.



\## 9. Módulo de incidencias



Las incidencias son eventos que afectan o pueden afectar la planilla.



Tipos mínimos:



\- Tardanza.

\- Falta injustificada.

\- Falta justificada.

\- Descanso médico.

\- Permiso.

\- Licencia con goce.

\- Licencia sin goce.

\- Vacaciones.

\- Horas extras.

\- Bono.

\- Comisión.

\- Adelanto.

\- Préstamo.

\- Descuento.

\- Reintegro.

\- Movilidad.

\- Alimentación.

\- Asignación.

\- Suspensión.

\- Cese.



\### Estados



\- Registrada.

\- Pendiente de aprobación.

\- Aprobada.

\- Rechazada.

\- Incluida en preplanilla.

\- Incluida en planilla cerrada.

\- Anulada.



\## 10. Conceptos de planilla



El sistema debe manejar conceptos configurables.



Cada concepto debe tener:



\- Código interno.

\- Nombre.

\- Tipo: ingreso, descuento, aporte trabajador, aporte empleador.

\- Naturaleza: remunerativo o no remunerativo.

\- Afecta AFP/ONP.

\- Afecta EsSalud.

\- Afecta renta de quinta categoría.

\- Afecta CTS.

\- Afecta gratificación.

\- Afecta vacaciones.

\- Afecta liquidación.

\- Fórmula.

\- Vigencia desde.

\- Vigencia hasta.

\- Estado.

\- Fuente normativa o supuesto interno.



\### Regla crítica



No hardcodear tasas, porcentajes ni fórmulas laborales directamente en componentes de frontend.



\## 11. Preplanilla



Antes de cerrar planilla debe existir una preplanilla.



La preplanilla debe mostrar:



\- Trabajadores activos del periodo.

\- Trabajadores ingresados en el mes.

\- Trabajadores cesados en el mes.

\- Sueldo base.

\- Días trabajados.

\- Días no trabajados.

\- Horas ordinarias.

\- Horas extras aprobadas.

\- Incidencias.

\- Ingresos.

\- Descuentos.

\- Aportes.

\- Neto estimado.

\- Observaciones.

\- Errores críticos.



\### Validaciones obligatorias



El sistema debe advertir o bloquear si existe:



\- Trabajador activo sin sueldo.

\- Trabajador activo sin fecha de ingreso.

\- Trabajador activo sin régimen pensionario.

\- Trabajador activo sin datos bancarios.

\- Trabajador con contrato vencido.

\- Horas extras pendientes de aprobación.

\- Faltas sin justificar.

\- Vacaciones sin saldo suficiente.

\- Neto a pagar negativo.

\- Descuento inusual.

\- Variación fuerte contra el mes anterior.

\- Cambio de sueldo sin motivo.

\- Cambio de sueldo sin auditoría.

\- Trabajador cesado incluido como activo.



\## 12. Cálculo de planilla



El sistema debe calcular:



\- Sueldo básico proporcional.

\- Días trabajados.

\- Días no trabajados.

\- Tardanzas.

\- Faltas.

\- Licencias.

\- Vacaciones.

\- Horas extras.

\- Bonos.

\- Comisiones.

\- Asignaciones.

\- Adelantos.

\- Préstamos.

\- Descuentos.

\- Aportes del trabajador.

\- Aportes del empleador.

\- Neto a pagar.



\### Regla



Todo cálculo debe poder ser explicado.



Cada monto calculado debe permitir ver:



\- Concepto.

\- Fórmula.

\- Base de cálculo.

\- Cantidad.

\- Resultado.

\- Fuente o regla aplicada.



\## 13. Cierre de planilla



La planilla debe tener estados.



Estados sugeridos:



\- Borrador.

\- En revisión.

\- Observada.

\- Aprobada por RRHH.

\- Aprobada por Finanzas.

\- Cerrada.

\- Pagada.

\- Reabierta.

\- Anulada.



\### Reglas



\- No se pueden generar boletas definitivas desde una planilla en borrador.

\- No se puede pagar una planilla no cerrada.

\- No se puede modificar libremente una planilla cerrada.

\- Toda reapertura requiere permiso especial.

\- Toda reapertura requiere motivo.

\- Toda reapertura debe dejar auditoría.



\## 14. Boletas de pago



El sistema debe permitir:



\- Generar boleta individual.

\- Generar boletas masivas.

\- Descargar PDF.

\- Enviar por correo.

\- Registrar fecha de generación.

\- Registrar fecha de envío.

\- Registrar si fue reemplazada.

\- Mantener historial de versiones.



La boleta debe mostrar:



\- Datos del empleador.

\- Datos del trabajador.

\- Periodo.

\- Cargo.

\- Fecha de ingreso.

\- Ingresos.

\- Descuentos.

\- Aportes.

\- Neto a pagar.

\- Observaciones.

\- Identificador o código interno.



\## 15. Pagos



El sistema debe permitir:



\- Generar resumen de pago.

\- Filtrar por banco.

\- Validar cuentas bancarias.

\- Exportar archivo o reporte para banco.

\- Registrar fecha de pago.

\- Adjuntar constancia de pago.

\- Marcar pagos observados.

\- Marcar pagos completados.



\## 16. Beneficios sociales



La arquitectura debe estar preparada para:



\- Gratificaciones.

\- CTS.

\- Vacaciones.

\- Utilidades, si corresponde.

\- Liquidación de beneficios sociales.

\- Vacaciones truncas.

\- Gratificación trunca.

\- CTS trunca.

\- Indemnización, si corresponde.

\- Provisiones mensuales.



No todos estos módulos tienen que estar en el MVP, pero el diseño de datos no debe impedir implementarlos después.



\## 17. Reportes mínimos



RRHH debe poder consultar:



\- Costo total de planilla.

\- Costo por área.

\- Costo por sede.

\- Comparativo mensual.

\- Trabajadores activos.

\- Altas y bajas.

\- Contratos por vencer.

\- Vacaciones pendientes.

\- Horas extras por trabajador.

\- Tardanzas por área.

\- Faltas por trabajador.

\- Descuentos.

\- Adelantos.

\- Préstamos.

\- Boletas generadas.

\- Planillas cerradas.

\- Pagos pendientes.

\- Pagos realizados.



\## 18. Roles y permisos



Roles mínimos:



\- Superadmin.

\- Administrador de empresa.

\- RRHH.

\- Finanzas.

\- Jefe de área.

\- Trabajador.

\- Auditor.



Permisos críticos:



\- Ver sueldos.

\- Editar sueldos.

\- Ver datos bancarios.

\- Editar datos bancarios.

\- Aprobar incidencias.

\- Aprobar horas extras.

\- Cerrar planilla.

\- Reabrir planilla.

\- Generar boletas.

\- Descargar reportes.

\- Ver auditoría.



\## 19. Portal del trabajador



Fase posterior recomendada.



Debe permitir:



\- Ver boletas.

\- Descargar boletas.

\- Solicitar vacaciones.

\- Solicitar permisos.

\- Subir descanso médico.

\- Ver asistencia.

\- Ver tardanzas.

\- Ver estado de solicitudes.

\- Actualizar datos personales sujetos a aprobación.



\## 20. Criterios de aceptación general



Una funcionalidad se considera completa si:



\- Tiene modelo de datos.

\- Tiene validaciones.

\- Tiene permisos.

\- Tiene auditoría.

\- Tiene tests.

\- Tiene impacto claro en preplanilla o planilla si corresponde.

\- Tiene documentación de supuestos normativos.

\- No depende de cálculos manuales en Excel.

