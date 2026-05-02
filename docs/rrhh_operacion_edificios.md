\# Operación de RRHH por edificios



\## 1. Contexto del negocio



El sistema está diseñado para una administradora de edificios que gestiona múltiples edificios, como mínimo 15.



La operación no depende únicamente de RRHH central. Cada edificio puede tener personal operativo asignado y uno o más administradores responsables de controlar asistencia, turnos, permisos, incidencias y novedades de planilla.



Actualmente puede existir una cantidad limitada de administradores, por ejemplo 5 administradores para 15 edificios. Un administrador puede encargarse de 2 o 3 edificios.



\## 2. Principio operativo



El sistema debe permitir que cada administrador gestione la preplanilla de los edificios bajo su responsabilidad.



RRHH no debe digitar toda la información desde cero. RRHH debe revisar, validar, observar, corregir y consolidar la información enviada por los administradores.



El flujo ideal es:



Edificio → Administrador → Preplanilla del edificio → Revisión RRHH → Consolidación → Pago → Boletas → Reportes.



\## 3. Entidades principales



\### Empresa administradora



Representa a la empresa que administra los edificios.



Datos sugeridos:



\- Razón social.

\- RUC.

\- Dirección fiscal.

\- Representante.

\- Régimen laboral usado.

\- Configuración de planilla.

\- Configuración de beneficios.

\- Usuarios internos.



\### Edificio



Representa cada edificio administrado.



Datos sugeridos:



\- Nombre del edificio.

\- Código interno.

\- Dirección.

\- Distrito.

\- Cliente o junta de propietarios.

\- Administrador responsable.

\- Estado: activo, suspendido, terminado.

\- Centro de costo.

\- Contacto del comité o junta.

\- Cuenta bancaria asociada, si aplica.

\- Configuración de turnos.

\- Personal asignado.



\### Administrador



Usuario operativo responsable de uno o varios edificios.



Debe poder:



\- Ver solo sus edificios asignados.

\- Ver el personal de sus edificios.

\- Registrar asistencia.

\- Registrar permisos.

\- Registrar emergencias.

\- Registrar reemplazos.

\- Registrar cambios de turno.

\- Registrar novedades de planilla.

\- Enviar preplanilla a RRHH.

\- Responder observaciones.



No debe poder:



\- Cambiar sueldos sin permiso.

\- Cerrar planilla general.

\- Modificar datos sensibles del trabajador sin autorización.

\- Ver sueldos de edificios que no administra.



\### Trabajador



Puede estar asignado a un edificio base, pero puede cubrir turnos o realizar labores temporales en otro edificio.



Datos adicionales necesarios:



\- Edificio base.

\- Puesto operativo.

\- Turno habitual.

\- Administrador responsable.

\- Historial de asignaciones.

\- Historial de coberturas.

\- Historial de permisos.

\- Historial de incidencias.

\- Centro de costo principal.



\## 4. Asignación del trabajador a edificio



Cada trabajador debe tener una asignación principal.



Ejemplo:



\- Trabajador: Juan Pérez.

\- Cargo: Conserje.

\- Edificio base: Edificio Los Álamos.

\- Turno: Noche.

\- Administrador responsable: Carlos.

\- Centro de costo: EDI-LOS-ALAMOS.



La asignación principal sirve para:



\- Control operativo.

\- Reportes por edificio.

\- Cálculo de costo por edificio.

\- Validación de asistencia.

\- Responsabilidad del administrador.

\- Preplanilla del edificio.



\## 5. Cobertura temporal en otro edificio



El sistema debe manejar casos donde un trabajador va a otro edificio por necesidad operativa.



Ejemplos:



\- Cubre descanso de otro trabajador.

\- Cubre falta.

\- Cubre vacaciones.

\- Apoya por emergencia.

\- Cubre turno nocturno.

\- Se desplaza por indicación del administrador.

\- Trabaja medio turno en un edificio y medio turno en otro.



Debe existir una entidad llamada Cobertura o Movimiento operativo.



\### Datos mínimos de cobertura



\- Trabajador.

\- Edificio origen.

\- Edificio destino.

\- Fecha.

\- Hora de inicio.

\- Hora de fin.

\- Motivo.

\- Administrador que solicita.

\- Administrador que aprueba.

\- Tipo de cobertura.

\- Si genera horas extra.

\- Si genera movilidad.

\- Si afecta costo del edificio destino.

\- Estado: solicitada, aprobada, rechazada, ejecutada, observada.

\- Evidencia o comentario.



\### Tipos de cobertura



\- Reemplazo por falta.

\- Reemplazo por descanso.

\- Reemplazo por vacaciones.

\- Apoyo por emergencia.

\- Cambio temporal de sede.

\- Turno adicional.

\- Apoyo parcial.

\- Cobertura nocturna.

\- Cobertura feriado.



\## 6. Movimiento entre edificios



No todo movimiento debe tratarse igual.



\### Caso A: mismo empleador



Si el trabajador pertenece a la misma empresa administradora y solo cambia temporalmente de edificio, el sistema debe registrar el movimiento operativo, el edificio destino, el turno cubierto y el impacto en preplanilla.



Debe mantenerse trazabilidad de dónde trabajó cada día.



\### Caso B: distinto empleador o edificio con planilla propia



Si cada edificio, junta o cliente actúa como empleador distinto, mover un trabajador de un edificio a otro puede tener implicancias laborales mayores.



En este caso el sistema no debe tratarlo como un simple cambio de turno. Debe marcarlo como caso sensible y requerir validación de RRHH/legal.



Regla:



Si el edificio origen y destino pertenecen a empleadores/RUC distintos, el sistema debe bloquear o advertir antes de aprobar la cobertura.



\## 7. Permisos, emergencias y salidas durante turno



El sistema debe permitir registrar situaciones reales de producción.



Tipos:



\- Permiso personal.

\- Permiso médico.

\- Emergencia familiar.

\- Salida anticipada.

\- Tardanza justificada.

\- Tardanza no justificada.

\- Falta justificada.

\- Falta injustificada.

\- Descanso médico.

\- Cambio de turno.

\- Abandono de turno.

\- Retiro por emergencia del edificio.

\- Comisión de servicio.

\- Apoyo externo.



\### Datos mínimos



\- Trabajador.

\- Edificio.

\- Fecha.

\- Hora de salida.

\- Hora de retorno, si aplica.

\- Motivo.

\- Tipo de permiso.

\- Con goce o sin goce.

\- Recupera horas: sí/no.

\- Documento adjunto, si aplica.

\- Administrador que registra.

\- Usuario que aprueba.

\- Impacto en planilla.

\- Comentario.



\## 8. Turnos por edificio



Cada edificio puede tener turnos diferentes.



Ejemplos:



\- Portería día.

\- Portería noche.

\- Limpieza mañana.

\- Limpieza tarde.

\- Mantenimiento.

\- Vigilancia.

\- Domingo o feriado.

\- Turnos rotativos.



El sistema debe permitir:



\- Crear turnos por edificio.

\- Asignar trabajadores a turnos.

\- Programar descansos.

\- Programar reemplazos.

\- Detectar huecos sin cobertura.

\- Detectar sobrecarga de horas.

\- Detectar conflictos de horario.

\- Detectar si una persona está asignada a dos edificios al mismo tiempo.



\## 9. Programación mensual



Antes del mes o semana operativa, el administrador debería poder armar una programación.



Debe incluir:



\- Trabajadores asignados.

\- Turnos.

\- Descansos.

\- Vacaciones programadas.

\- Reemplazos.

\- Coberturas.

\- Observaciones.



El sistema debe alertar:



\- Edificio sin conserje en un turno.

\- Trabajador duplicado en dos edificios.

\- Trabajador sin descanso.

\- Trabajador con exceso de horas.

\- Turno sin responsable.

\- Cobertura sin aprobación.



\## 10. Parte diario del edificio



Cada edificio debe tener un parte diario operativo.



Debe registrar:



\- Personal programado.

\- Personal que asistió.

\- Personal que faltó.

\- Reemplazos.

\- Permisos.

\- Emergencias.

\- Incidentes.

\- Horas extras.

\- Observaciones del administrador.

\- Evidencias.



El parte diario debe alimentar la preplanilla del edificio.



\## 11. Preplanilla por edificio



Cada administrador debe poder generar la preplanilla de sus edificios.



La preplanilla por edificio debe mostrar:



\- Trabajadores asignados.

\- Días programados.

\- Días trabajados.

\- Faltas.

\- Tardanzas.

\- Permisos.

\- Licencias.

\- Descansos médicos.

\- Vacaciones.

\- Horas extras.

\- Coberturas en otros edificios.

\- Coberturas recibidas desde otros edificios.

\- Bonos.

\- Descuentos.

\- Movilidad.

\- Observaciones.

\- Neto estimado, si el administrador tiene permiso para verlo.

\- Estado de revisión.



\## 12. Envío de preplanilla a RRHH



El administrador debe enviar la preplanilla del edificio a RRHH.



Estados sugeridos:



\- Borrador.

\- En revisión del administrador.

\- Enviada a RRHH.

\- Observada por RRHH.

\- Corregida por administrador.

\- Aprobada por RRHH.

\- Consolidada.

\- Cerrada.



Reglas:



\- No se puede enviar una preplanilla con turnos sin revisar.

\- No se puede enviar si hay coberturas pendientes.

\- No se puede enviar si hay faltas sin clasificar.

\- No se puede enviar si hay horas extras sin aprobación.

\- Toda corrección posterior al envío debe dejar historial.



\## 13. Observaciones de RRHH



RRHH debe poder observar una preplanilla.



Motivos de observación:



\- Falta sin justificar.

\- Permiso sin sustento.

\- Horas extras no aprobadas.

\- Trabajador duplicado.

\- Cobertura no sustentada.

\- Turno incompleto.

\- Trabajador asignado a edificio incorrecto.

\- Diferencia contra asistencia.

\- Diferencia contra programación.

\- Falta documento.

\- Posible exceso de jornada.



El administrador debe corregir y reenviar.



\## 14. Consolidación central



RRHH debe consolidar todas las preplanillas de edificios.



La vista central debe mostrar:



\- Edificios pendientes de envío.

\- Edificios enviados.

\- Edificios observados.

\- Edificios aprobados.

\- Trabajadores con movimientos entre edificios.

\- Trabajadores con horas extras.

\- Trabajadores con permisos.

\- Trabajadores con faltas.

\- Trabajadores duplicados.

\- Total estimado por edificio.

\- Total estimado general.

\- Variación contra mes anterior.



\## 15. Costo por edificio



El sistema debe permitir calcular o reportar el costo por edificio.



Debe considerar:



\- Trabajadores asignados al edificio.

\- Coberturas recibidas.

\- Coberturas prestadas a otros edificios.

\- Horas extras.

\- Bonos.

\- Movilidad.

\- Descuentos.

\- Prorrateos.



Ejemplo:



Si Juan pertenece al Edificio A pero cubrió 2 turnos en el Edificio B, el sistema debe permitir decidir si ese costo se queda en el Edificio A o se carga al Edificio B.



\## 16. Reglas de prorrateo



El sistema debe permitir configurar cómo se reparte el costo cuando un trabajador labora en más de un edificio.



Opciones:



\- Todo al edificio base.

\- Todo al edificio destino.

\- Por horas trabajadas.

\- Por días trabajados.

\- Manual con aprobación.

\- Según contrato del cliente.



Toda regla de prorrateo debe ser visible y auditable.



\## 17. Alertas operativas



El sistema debe alertar:



\- Edificio sin personal en turno.

\- Trabajador asignado a dos edificios al mismo tiempo.

\- Trabajador con exceso de horas.

\- Trabajador sin descanso registrado.

\- Horas extras sin aprobación.

\- Permiso sin sustento.

\- Falta sin reemplazo.

\- Emergencia sin cierre.

\- Administrador con preplanilla pendiente.

\- Edificio sin preplanilla enviada.

\- Cobertura entre edificios sin aprobación.

\- Trabajador enviado a edificio de otro empleador/RUC.



\## 18. Roles y permisos por edificio



\### Superadmin



Puede ver y configurar todo.



\### RRHH central



Puede ver todos los edificios, trabajadores, preplanillas, incidencias y consolidación.



\### Finanzas



Puede ver montos aprobados, reportes, pagos y costos por edificio.



\### Administrador de edificio



Puede ver solo sus edificios asignados.



Puede registrar:



\- Asistencia.

\- Permisos.

\- Incidencias.

\- Coberturas.

\- Observaciones.

\- Preplanilla.



No debe poder cerrar planilla general.



\### Supervisor o jefe operativo



Puede aprobar coberturas, cambios de turno y emergencias.



\### Trabajador



Puede ver su asistencia, boletas y solicitudes si existe portal.



\## 19. Auditoría obligatoria



Debe auditarse:



\- Cambio de edificio base.

\- Cobertura en otro edificio.

\- Cambio de turno.

\- Permiso.

\- Falta.

\- Emergencia.

\- Corrección de asistencia.

\- Aprobación de horas extras.

\- Envío de preplanilla.

\- Observación de RRHH.

\- Corrección de preplanilla.

\- Aprobación final.

\- Cambio de regla de prorrateo.

\- Cambio de administrador responsable.



\## 20. Reportes necesarios



Reportes por edificio:



\- Personal asignado.

\- Asistencia mensual.

\- Faltas.

\- Tardanzas.

\- Permisos.

\- Horas extras.

\- Coberturas recibidas.

\- Coberturas enviadas.

\- Costo laboral.

\- Variación mensual.

\- Preplanilla enviada.

\- Observaciones de RRHH.



Reportes generales:



\- Estado de preplanillas por edificio.

\- Costo total por edificio.

\- Costo total empresa.

\- Trabajadores con más movimientos.

\- Trabajadores con más horas extras.

\- Edificios con más incidencias.

\- Administradores con más observaciones.

\- Edificios pendientes de cierre.

