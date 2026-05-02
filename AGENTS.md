\# AGENTS.md



\## 1. Contexto general del proyecto



Este proyecto es un sistema de asistencia, operación de edificios, RRHH y preplanilla/planilla para una administradora de edificios en Perú.



La empresa administra múltiples edificios. Como mínimo debe soportar 15 edificios, aunque la arquitectura debe permitir crecer a más edificios sin rediseñar el sistema.



La operación real no depende únicamente de RRHH central. Existen administradores de edificios. Un administrador puede encargarse de 1, 2, 3 o más edificios. Estos administradores controlan la operación diaria del personal asignado a cada edificio.



El sistema debe cubrir:



\- Edificios administrados.

\- Administradores asignados a edificios.

\- Personal asignado a edificios.

\- Turnos por edificio.

\- Asistencia.

\- Tardanzas.

\- Faltas.

\- Permisos.

\- Emergencias.

\- Cambios de turno.

\- Coberturas entre edificios.

\- Horas extras.

\- Parte diario operativo.

\- Preplanilla por edificio.

\- Revisión y observación de RRHH.

\- Consolidación central.

\- Pago por Finanzas o responsable de pago.

\- Boletas.

\- Reportes.

\- Auditoría.



El flujo real del negocio es:



Edificio → Administrador → Asistencia / Incidencias / Parte diario → Preplanilla del edificio → RRHH revisa y consolida → Finanzas o responsable paga → Boletas y reportes.



\## 2. Regla principal del proyecto



Toda funcionalidad relacionada con trabajadores, asistencia, turnos, sueldos, descuentos, beneficios sociales, boletas, preplanilla, planilla, pagos o liquidaciones debe diseñarse considerando normativa peruana aplicable.



Fuentes normativas base:



\- SUNAFIL.

\- Ministerio de Trabajo y Promoción del Empleo.

\- SUNAT Planilla Electrónica.

\- T-Registro.

\- PLAME.

\- EsSalud.

\- AFP / ONP.

\- Normativa de seguridad y salud en el trabajo cuando corresponda.

\- Normativa sobre intermediación, desplazamiento o destaque de personal cuando corresponda.

\- Normativa sobre beneficios sociales cuando corresponda.



Si una regla normativa no está validada, debe marcarse como:



SUPUESTO PENDIENTE DE VALIDACIÓN LEGAL.



No inventar reglas legales. No asumir porcentajes, plazos, tasas o fórmulas sin fuente o sin dejarlas parametrizadas.



\## 3. Separación obligatoria: operación, RRHH y planilla



El sistema debe separar tres capas:



\### 3.1 Operación por edificio



Esta capa controla lo que ocurre día a día en cada edificio.



Incluye:



\- Programación de turnos.

\- Asistencia.

\- Parte diario.

\- Permisos.

\- Emergencias.

\- Faltas.

\- Reemplazos.

\- Coberturas.

\- Horas extras.

\- Observaciones del administrador.

\- Personal que cubre en otro edificio.



\### 3.2 Preplanilla por edificio



Esta capa transforma la operación en información revisable para RRHH.



Incluye:



\- Días trabajados.

\- Días no trabajados.

\- Tardanzas.

\- Faltas.

\- Permisos.

\- Licencias.

\- Descansos médicos.

\- Vacaciones.

\- Horas extras aprobadas.

\- Coberturas recibidas.

\- Coberturas enviadas.

\- Bonos.

\- Descuentos.

\- Movilidad.

\- Observaciones.

\- Estado de revisión del administrador.

\- Estado de revisión de RRHH.



\### 3.3 Planilla central



Esta capa consolida lo aprobado por edificio y prepara el cierre.



Incluye:



\- Trabajadores incluidos.

\- Conceptos remunerativos.

\- Conceptos no remunerativos.

\- Descuentos.

\- Aportes.

\- Neto a pagar.

\- Boletas.

\- Pagos.

\- Reportes.

\- Cierre.

\- Reapertura excepcional.

\- Auditoría.



\## 4. Separación obligatoria: T-Registro y PLAME



El sistema debe distinguir información laboral estructural e información mensual de pagos.



\### 4.1 Información tipo T-Registro



Información estable o estructural del trabajador.



Incluye:



\- Datos personales.

\- Datos laborales.

\- Fecha de ingreso.

\- Fecha de cese.

\- Tipo de trabajador.

\- Régimen laboral.

\- Establecimiento o edificio donde labora.

\- Seguridad social.

\- Sistema pensionario.

\- Derechohabientes, si se implementa.

\- Alta.

\- Baja.

\- Modificaciones.



\### 4.2 Información tipo PLAME



Información mensual del periodo.



Incluye:



\- Remuneraciones.

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

\- Periodo laboral/tributario.



Regla:



No mezclar datos estructurales del trabajador con datos mensuales de planilla. Todo dato mensual debe estar asociado a un periodo.



\## 5. Documentos funcionales obligatorios



Antes de modificar código relacionado con RRHH, asistencia, edificios, preplanilla o planilla, Codex debe leer estos documentos si existen:



\- docs/rrhh\_planilla\_peru\_requisitos.md

\- docs/rrhh\_normativa\_peru\_matriz.md

\- docs/rrhh\_checklist\_auditoria.md

\- docs/rrhh\_tests\_obligatorios.md

\- docs/rrhh\_flujo\_cierre\_planilla.md

\- docs/rrhh\_operacion\_edificios.md



Si un documento no existe o está vacío, Codex debe indicarlo en su respuesta antes de proponer cambios.



No implementar reglas laborales críticas si no están documentadas o si no se marca claramente el supuesto.



\## 6. Entidades principales del dominio



El sistema debe contemplar, como mínimo, estas entidades o equivalentes:



\### Empresa administradora



Representa a la empresa que administra edificios.



Debe tener:



\- Razón social.

\- RUC.

\- Dirección fiscal.

\- Configuración de planilla.

\- Configuración laboral.

\- Usuarios internos.

\- Estado.



\### Edificio



Representa cada edificio administrado.



Debe tener:



\- Nombre.

\- Código interno.

\- Dirección.

\- Distrito.

\- Cliente, comité o junta.

\- Administrador responsable.

\- Estado.

\- Centro de costo.

\- Configuración de turnos.

\- Personal asignado.

\- RUC/empleador asociado si corresponde.



\### Administrador de edificio



Usuario operativo responsable de uno o más edificios.



Debe poder:



\- Ver sus edificios asignados.

\- Ver personal de sus edificios.

\- Registrar asistencia.

\- Registrar permisos.

\- Registrar emergencias.

\- Registrar coberturas.

\- Registrar cambios de turno.

\- Registrar observaciones.

\- Generar preplanilla del edificio.

\- Enviar preplanilla a RRHH.

\- Corregir observaciones de RRHH.



No debe poder:



\- Cerrar planilla general.

\- Modificar sueldos sin permiso.

\- Cambiar datos sensibles del trabajador sin autorización.

\- Ver sueldos de edificios que no administra.

\- Reabrir planillas cerradas.



\### Trabajador



Persona que presta servicios en uno o más edificios.



Debe tener:



\- Datos personales.

\- Datos laborales.

\- Edificio base.

\- Cargo.

\- Turno habitual.

\- Administrador responsable.

\- Centro de costo principal.

\- Estado laboral.

\- Historial de asignaciones.

\- Historial de coberturas.

\- Historial de permisos.

\- Historial de incidencias.



\### Turno



Programación horaria asociada a edificio y trabajador.



Debe tener:



\- Edificio.

\- Trabajador.

\- Fecha.

\- Hora inicio.

\- Hora fin.

\- Tipo de turno.

\- Estado.

\- Descanso asociado si aplica.

\- Reemplazo si aplica.



\### Parte diario



Registro operativo diario del edificio.



Debe tener:



\- Edificio.

\- Fecha.

\- Administrador responsable.

\- Personal programado.

\- Personal asistente.

\- Tardanzas.

\- Faltas.

\- Permisos.

\- Reemplazos.

\- Emergencias.

\- Incidencias.

\- Observaciones.

\- Evidencias.



\### Cobertura entre edificios



Movimiento temporal de un trabajador hacia otro edificio.



Debe tener:



\- Trabajador.

\- Edificio origen.

\- Edificio destino.

\- Fecha.

\- Hora inicio.

\- Hora fin.

\- Motivo.

\- Tipo de cobertura.

\- Administrador solicitante.

\- Administrador aprobador.

\- Si genera horas extra.

\- Si genera movilidad.

\- Si afecta costo del edificio destino.

\- Estado.

\- Evidencia.

\- Comentario.



Tipos de cobertura:



\- Reemplazo por falta.

\- Reemplazo por descanso.

\- Reemplazo por vacaciones.

\- Apoyo por emergencia.

\- Cambio temporal de sede.

\- Turno adicional.

\- Apoyo parcial.

\- Cobertura nocturna.

\- Cobertura en feriado.



\### Incidencia



Evento que afecta asistencia, operación o planilla.



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

\- Emergencia.

\- Cambio de turno.

\- Cobertura en otro edificio.



Estados mínimos:



\- Registrada.

\- Pendiente de aprobación.

\- Aprobada.

\- Rechazada.

\- Observada.

\- Anulada.

\- Incluida en preplanilla.

\- Incluida en planilla cerrada.



\### Preplanilla de edificio



Documento operativo mensual/semanal enviado por el administrador a RRHH.



Debe tener:



\- Edificio.

\- Periodo.

\- Administrador.

\- Trabajadores incluidos.

\- Asistencia resumida.

\- Incidencias.

\- Coberturas.

\- Permisos.

\- Horas extras.

\- Observaciones.

\- Estado.

\- Historial de envío.

\- Historial de observaciones.



\### Planilla central



Consolidado final validado por RRHH y Finanzas.



Debe tener:



\- Periodo.

\- Trabajadores incluidos.

\- Edificios incluidos.

\- Preplanillas origen.

\- Conceptos.

\- Ingresos.

\- Descuentos.

\- Aportes.

\- Neto a pagar.

\- Estado.

\- Auditoría.

\- Boletas.

\- Pagos.



\## 7. Reglas críticas sobre edificios y empleadores



Si todos los trabajadores pertenecen al mismo empleador/RUC de la empresa administradora, una cobertura temporal entre edificios puede registrarse como movimiento operativo interno, siempre con autorización, asistencia, horario e impacto en preplanilla.



Si el edificio origen y el edificio destino pertenecen a empleadores/RUC distintos, el sistema no debe tratararlo como un simple cambio de turno.



Regla obligatoria:



Si edificio\_origen.empleador\_ruc != edificio\_destino.empleador\_ruc:



\- Marcar movimiento como sensible.

\- Requerir validación de RRHH.

\- Requerir validación legal o administrativa si aplica.

\- Bloquear aprobación automática.

\- Bloquear cierre de preplanilla si no está validado.

\- Dejar auditoría reforzada.



No ocultar este caso. No asumir que siempre es legal o permitido.



\## 8. Turnos y programación



Cada edificio puede tener turnos distintos.



El sistema debe permitir:



\- Crear turnos por edificio.

\- Asignar trabajadores a turnos.

\- Programar descansos.

\- Programar reemplazos.

\- Programar coberturas.

\- Detectar huecos sin cobertura.

\- Detectar personal duplicado.

\- Detectar solapamiento de horarios.

\- Detectar exceso de horas.

\- Detectar trabajador en dos edificios al mismo tiempo.

\- Detectar turno sin responsable.



Validaciones mínimas:



\- Un trabajador no puede estar asignado a dos turnos solapados.

\- Un trabajador no puede cubrir dos edificios al mismo tiempo.

\- Una cobertura debe tener motivo.

\- Una cobertura debe tener edificio origen y destino.

\- Una cobertura sensible debe requerir aprobación especial.

\- Las horas extras deben requerir aprobación antes de pasar a planilla.



\## 9. Permisos, emergencias y salidas durante turno



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



Cada registro debe tener:



\- Trabajador.

\- Edificio.

\- Fecha.

\- Hora de salida.

\- Hora de retorno si aplica.

\- Motivo.

\- Tipo.

\- Con goce o sin goce si aplica.

\- Si recupera horas.

\- Documento adjunto si aplica.

\- Usuario que registra.

\- Usuario que aprueba.

\- Impacto en preplanilla.

\- Impacto en planilla.

\- Comentario.



Regla:



Toda salida, permiso o emergencia que afecte jornada, asistencia o pago debe quedar auditada.



\## 10. Preplanilla por edificio



Cada administrador debe poder generar y enviar la preplanilla de sus edificios.



Estados sugeridos:



\- Borrador.

\- En revisión del administrador.

\- Enviada a RRHH.

\- Observada por RRHH.

\- Corregida por administrador.

\- Aprobada por RRHH.

\- Consolidada.

\- Cerrada.



La preplanilla debe mostrar:



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

\- Estado de revisión.

\- Neto estimado solo si el usuario tiene permiso para verlo.



Reglas:



\- No enviar preplanilla con coberturas pendientes.

\- No enviar preplanilla con faltas sin clasificar.

\- No enviar preplanilla con horas extras sin aprobación.

\- No enviar preplanilla con turnos críticos sin revisar.

\- No consolidar preplanilla observada.

\- Toda corrección después del envío debe dejar historial.



\## 11. Observaciones de RRHH



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

\- Movimiento entre RUC distintos sin validación.

\- Neto estimado inusual.

\- Variación inusual contra periodo anterior.



El administrador debe poder corregir y reenviar.



Toda observación debe tener:



\- Motivo.

\- Usuario que observa.

\- Fecha.

\- Comentario.

\- Estado.

\- Respuesta del administrador.

\- Evidencia si aplica.



\## 12. Consolidación central RRHH



RRHH debe tener una vista central para consolidar las preplanillas.



Debe mostrar:



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

\- Alertas críticas.

\- Preplanillas listas para consolidar.



Regla:



La planilla central no debe cerrarse si existen preplanillas críticas pendientes, observadas o inconsistentes.



\## 13. Costo por edificio y prorrateo



El sistema debe permitir calcular o reportar costo por edificio.



Debe considerar:



\- Personal asignado al edificio.

\- Coberturas recibidas.

\- Coberturas enviadas.

\- Horas extras.

\- Bonos.

\- Movilidad.

\- Descuentos.

\- Prorrateos.



Reglas de prorrateo permitidas:



\- Todo al edificio base.

\- Todo al edificio destino.

\- Por horas trabajadas.

\- Por días trabajados.

\- Manual con aprobación.

\- Según contrato del cliente.



Toda regla de prorrateo debe ser visible, configurable y auditable.



No hardcodear la regla de prorrateo en el frontend.



\## 14. Conceptos de planilla



Los conceptos deben ser configurables.



Cada concepto debe tener:



\- Código interno.

\- Nombre.

\- Tipo: ingreso, descuento, aporte trabajador, aporte empleador.

\- Naturaleza: remunerativo o no remunerativo.

\- Si afecta AFP/ONP.

\- Si afecta EsSalud.

\- Si afecta renta de quinta categoría.

\- Si afecta CTS.

\- Si afecta gratificación.

\- Si afecta vacaciones.

\- Si afecta liquidación.

\- Fórmula o regla de cálculo.

\- Vigencia desde.

\- Vigencia hasta.

\- Estado.

\- Fuente normativa o supuesto interno.



Reglas:



\- No hardcodear tasas, porcentajes ni fórmulas laborales en componentes UI.

\- No calcular planilla solo en frontend.

\- Todo cálculo sensible debe estar en backend o capa de dominio testeable.

\- Todo cálculo debe poder explicarse.

\- Cada monto debe poder mostrar concepto, base, cantidad, fórmula y resultado.



\## 15. Cierre de planilla



La planilla debe tener estados.



Estados sugeridos:



\- Borrador.

\- En revisión.

\- Observada.

\- Validada por RRHH.

\- Validada por Finanzas.

\- Cerrada.

\- Pagada.

\- Reabierta.

\- Anulada.



Reglas:



\- No generar boletas definitivas desde planilla en borrador.

\- No pagar una planilla no cerrada.

\- No modificar libremente una planilla cerrada.

\- Toda reapertura requiere permiso especial.

\- Toda reapertura requiere motivo.

\- Toda reapertura debe conservar versión anterior.

\- Toda reapertura debe dejar auditoría.

\- Si la reapertura cambia montos, las boletas anteriores deben quedar reemplazadas o anuladas, no eliminadas.



\## 16. Beneficios sociales



La arquitectura debe estar preparada para:



\- Gratificaciones.

\- CTS.

\- Vacaciones.

\- Utilidades cuando corresponda.

\- Seguridad social.

\- Sistema pensionario.

\- Seguro Vida Ley.

\- SCTR cuando corresponda.

\- Liquidación de beneficios sociales.

\- Vacaciones truncas.

\- Gratificación trunca.

\- CTS trunca.

\- Indemnización si corresponde.

\- Provisiones mensuales.



No todos estos módulos tienen que estar en el MVP, pero el diseño de datos no debe impedir implementarlos después.



\## 17. Roles y permisos



Roles mínimos:



\- Superadmin.

\- Administrador de empresa.

\- RRHH central.

\- Finanzas.

\- Administrador de edificio.

\- Supervisor operativo.

\- Trabajador.

\- Auditor.



Permisos críticos:



\- Ver edificios asignados.

\- Ver todos los edificios.

\- Registrar asistencia.

\- Corregir asistencia.

\- Registrar permisos.

\- Aprobar permisos.

\- Registrar coberturas.

\- Aprobar coberturas.

\- Registrar emergencias.

\- Enviar preplanilla.

\- Observar preplanilla.

\- Aprobar preplanilla.

\- Consolidar preplanilla.

\- Ver sueldos.

\- Editar sueldos.

\- Ver datos bancarios.

\- Editar datos bancarios.

\- Cerrar planilla.

\- Reabrir planilla.

\- Generar boletas.

\- Preparar pagos.

\- Ver reportes.

\- Ver auditoría.



Reglas:



\- Un administrador de edificio solo debe ver sus edificios asignados.

\- Un administrador no debe ver sueldos si no tiene permiso explícito.

\- Un administrador no debe cerrar planilla general.

\- Finanzas no debe modificar asistencia operativa.

\- RRHH no debe perder trazabilidad de cambios realizados por administradores.

\- Auditor solo debe tener lectura.



\## 18. Auditoría obligatoria



Todo cambio sensible debe dejar auditoría.



Debe auditarse:



\- Alta de trabajador.

\- Baja de trabajador.

\- Cambio de sueldo.

\- Cambio de cargo.

\- Cambio de edificio base.

\- Cambio de turno.

\- Cambio de cuenta bancaria.

\- Cambio de régimen pensionario.

\- Corrección de asistencia.

\- Registro manual de asistencia.

\- Permiso.

\- Emergencia.

\- Falta.

\- Cobertura en otro edificio.

\- Aprobación de cobertura.

\- Rechazo de cobertura.

\- Aprobación de horas extras.

\- Envío de preplanilla.

\- Observación de RRHH.

\- Corrección de preplanilla.

\- Aprobación de preplanilla.

\- Consolidación.

\- Cierre de planilla.

\- Reapertura de planilla.

\- Generación de boletas.

\- Preparación de pagos.

\- Cambio de regla de prorrateo.

\- Cambio de administrador responsable.



Cada auditoría debe registrar:



\- Usuario.

\- Fecha y hora.

\- Acción.

\- Entidad afectada.

\- Valor anterior.

\- Valor nuevo.

\- Motivo.

\- Documento de respaldo si aplica.

\- IP o contexto técnico si existe.

\- Módulo afectado.



\## 19. Validaciones críticas



El sistema debe bloquear o advertir según corresponda.



Errores críticos bloqueantes:



\- Trabajador activo sin sueldo.

\- Trabajador activo sin fecha de ingreso.

\- Trabajador activo sin régimen pensionario.

\- Trabajador sin edificio base.

\- Trabajador sin turno asignado si corresponde.

\- Trabajador asignado a dos edificios al mismo tiempo.

\- Cobertura pendiente en periodo a cerrar.

\- Movimiento entre RUC distintos sin validación.

\- Horas extras sin aprobación.

\- Falta sin clasificar.

\- Preplanilla observada.

\- Preplanilla no enviada.

\- Planilla sin trabajadores.

\- Fórmula de concepto inválida.

\- Neto negativo.

\- Edición de planilla cerrada sin reapertura.

\- Usuario sin permiso intentando cerrar planilla.



Advertencias:



\- Contrato por vencer.

\- Variación fuerte contra mes anterior.

\- Muchas tardanzas.

\- Muchas faltas.

\- Muchas horas extras.

\- Trabajador nuevo sin documentos completos.

\- Cuenta bancaria no validada.

\- Edificio con muchas incidencias.

\- Administrador con muchas observaciones.

\- Costo por edificio mayor al mes anterior.



\## 20. Reportes mínimos



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

\- Estado de cierre del edificio.



Reportes generales:



\- Estado de preplanillas por edificio.

\- Edificios pendientes.

\- Edificios observados.

\- Costo total por edificio.

\- Costo total empresa.

\- Trabajadores con más movimientos.

\- Trabajadores con más horas extras.

\- Edificios con más incidencias.

\- Administradores con más observaciones.

\- Trabajadores duplicados en programación.

\- Pagos pendientes.

\- Planillas cerradas.

\- Planillas reabiertas.

\- Boletas generadas.



\## 21. Reglas técnicas



\- No implementar lógica laboral crítica solo en frontend.

\- Separar dominio, servicios, API y UI.

\- Crear tests cuando se toque lógica de asistencia, incidencias, preplanilla, planilla, pagos o auditoría.

\- Usar migraciones para cambios de base de datos.

\- No eliminar datos laborales sensibles; preferir estados, anulaciones o registros históricos.

\- No hacer cambios destructivos sin explicar impacto.

\- No modificar reglas de cálculo sin tests.

\- No introducir campos monetarios editables sin auditoría.

\- No mezclar conceptos remunerativos y no remunerativos.

\- No asumir que un campo de UI es suficiente para cumplir una obligación laboral.

\- No implementar integraciones reales con SUNAT, bancos o AFP sin capa de abstracción y validación explícita.



\## 22. Comandos de desarrollo



Codex debe detectar el stack real del proyecto antes de ejecutar comandos.



Si existe backend Python:



\- Revisar requirements.txt, pyproject.toml o Pipfile.

\- Preferir pytest para pruebas.

\- No inventar comandos si no existen.

\- Si hay FastAPI, revisar routers, schemas, models, services y tests.



Si existe frontend JavaScript/TypeScript:



\- Revisar package.json.

\- Usar el package manager detectado: npm, pnpm, yarn o bun.

\- Ejecutar lint/test/build solo si existen scripts definidos.

\- No cambiar librerías visuales sin motivo.



Si existe base de datos:



\- Revisar migraciones existentes.

\- No modificar esquema sin migración.

\- No borrar columnas sin plan de migración.

\- No romper datos históricos de asistencia, preplanilla o planilla.



\## 23. Antes de modificar código



Codex debe hacer primero una auditoría breve.



Debe responder:



1\. Qué módulo se tocará.

2\. Qué flujo operativo afecta.

3\. Si afecta edificio, asistencia, preplanilla, planilla, pagos o boletas.

4\. Si toca normativa laboral peruana.

5\. Qué archivos piensa revisar.

6\. Qué riesgos ve.

7\. Qué tests deberían existir.



Si el usuario pidió explícitamente implementar, después de la auditoría puede modificar código.



Si el usuario pidió solo analizar, no modificar código.



\## 24. Antes de finalizar cualquier cambio



Codex debe verificar:



\- Tests relevantes pasan o explicar por qué no se ejecutaron.

\- No se rompió cálculo de planilla.

\- No se perdió trazabilidad.

\- No se introdujeron montos editables sin auditoría.

\- No se mezclaron conceptos remunerativos y no remunerativos.

\- No se agregó una regla laboral sin documentar fuente o supuesto.

\- No se permitió cierre de planilla con errores críticos.

\- No se permitió consolidar preplanillas observadas.

\- No se permitió cobertura entre edificios/RUC distintos sin validación.

\- No se rompieron permisos por edificio.

\- No se expusieron sueldos a usuarios no autorizados.

\- No se eliminaron datos históricos.



\## 25. Formato de respuesta esperado de Codex



Cuando Codex audite, debe responder con:



\- Resumen ejecutivo.

\- Huecos funcionales.

\- Riesgos operativos.

\- Riesgos normativos.

\- Riesgos de cálculo.

\- Riesgos de permisos.

\- Riesgos de auditoría.

\- Archivos revisados.

\- Archivos que habría que modificar.

\- Cambios propuestos.

\- Tests necesarios.

\- Orden recomendado de implementación.

\- Supuestos pendientes de validación legal.



Cuando Codex implemente, debe responder con:



\- Qué cambió.

\- Archivos modificados.

\- Por qué se cambió.

\- Qué validaciones se agregaron.

\- Qué auditoría se agregó.

\- Qué tests se agregaron.

\- Comandos ejecutados.

\- Resultado de tests.

\- Pendientes.



\## 26. Prioridad de implementación recomendada



No construir primero solo una planilla general.



Prioridad correcta:



1\. Edificios.

2\. Administradores asignados a edificios.

3\. Personal por edificio.

4\. Turnos por edificio.

5\. Asistencia.

6\. Permisos, emergencias e incidencias.

7\. Coberturas entre edificios.

8\. Parte diario.

9\. Preplanilla por edificio.

10\. Observaciones de RRHH.

11\. Consolidación central.

12\. Cálculo de planilla.

13\. Boletas.

14\. Pagos.

15\. Reportes.

16\. Beneficios sociales avanzados.

17\. Integraciones externas.



El sistema debe nacer desde la operación real del edificio y no solo desde una tabla de planilla.

## Alcance prohibido: facturación comercial



Este proyecto no es un sistema de facturación electrónica de ventas.



No implementar salvo instrucción explícita:



\- Facturas electrónicas de venta.

\- Boletas de venta electrónicas.

\- Notas de crédito comerciales.

\- Notas de débito comerciales.

\- Guías de remisión.

\- Series de comprobantes comerciales.

\- Envío de comprobantes de venta a SUNAT.

\- Catálogo de productos o servicios facturables.

\- Cálculo de IGV de ventas.

\- PDF de factura comercial.

\- Integración directa con facturador electrónico.



El sistema sí puede generar:



\- Boletas de pago de remuneraciones.

\- Resumen de pago de sueldos.

\- Lotes de pago.

\- Constancias de depósito.

\- Reportes de costo laboral por edificio.

\- Exportaciones para RRHH, Finanzas o contador.

\- Reportes para que otra área facture externamente en su facturador.



Diferencia obligatoria:

## Alcance prohibido: facturacion comercial

Este proyecto no debe convertirse en un sistema de facturacion electronica comercial ni en un facturador de ventas.

Terminos, tablas, rutas y modulos prohibidos salvo aprobacion explicita de alcance:

- invoices
- billing
- tax_invoice
- sales_invoice
- factura
- comprobante comercial
- boleta de venta
- nota de credito comercial
- nota de debito comercial
- guia de remision
- IGV de ventas
- series de comprobantes
- envio SUNAT de comprobantes comerciales

Permitido dentro del alcance laboral/remunerativo:

- payroll_payslips
- salary_payment_batches
- salary_payment_items
- building_cost_reports
- exportaciones internas para RRHH, Finanzas o contador

Las boletas del sistema son boletas de pago de remuneraciones para trabajadores. Los pagos del sistema son pagos de sueldos. Cualquier facturacion hacia clientes, comites o edificios debe ocurrir fuera del sistema en un facturador externo.



\- Boleta de pago: documento laboral/remunerativo entregado al trabajador.

\- Boleta de venta: comprobante de pago comercial emitido a un cliente.



Dentro de este proyecto, “boleta” debe referirse siempre a “boleta de pago de remuneraciones”. Si se requiere hablar de comprobantes comerciales, debe marcarse como integración externa futura.

