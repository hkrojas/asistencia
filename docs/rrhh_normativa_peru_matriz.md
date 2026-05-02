\# Matriz normativa RRHH / Planilla Perú



\## 1. Planilla Electrónica



Fuente base:

\- SUNAT - Planilla Electrónica

\- T-Registro

\- PLAME



Requisito funcional:

El sistema debe separar información laboral estructural del trabajador y la información mensual de pagos.



Implicancia en el sistema:

\- Datos del trabajador, contrato, régimen laboral, seguridad social y derechohabientes pertenecen al bloque tipo T-Registro.

\- Remuneraciones, descuentos, aportes, tributos, días trabajados e ingresos mensuales pertenecen al bloque tipo PLAME.



Estado:

Pendiente / En desarrollo / Implementado



Módulos afectados:

\- Trabajadores

\- Contratos

\- Planilla mensual

\- Boletas

\- Reportes

## 2. Alta, baja y modificación del trabajador



Requisito funcional:

El sistema debe registrar alta, baja y modificación de datos laborales con fecha, usuario responsable y motivo.



Datos mínimos:

\- Fecha de ingreso

\- Fecha de cese

\- Tipo de trabajador

\- Régimen laboral

\- Datos de seguridad social

\- Datos bancarios

\- Teléfono

\- Correo

\- Estado laboral



Validaciones:

\- No permitir incluir en planilla a un trabajador activo sin datos laborales mínimos.

\- No permitir cerrar planilla si hay trabajadores activos sin régimen pensionario o datos incompletos críticos.

\- Registrar historial de modificaciones.

## 3. Beneficios sociales



Fuente base:

\- SUNAFIL

\- MTPE



Beneficios que el sistema debe considerar:

\- Gratificaciones

\- CTS

\- Vacaciones

\- Utilidades cuando corresponda

\- Seguridad social en salud

\- Sistema pensionario: SNP u ONP / SPP o AFP

\- Seguro Vida Ley

\- SCTR cuando la actividad lo exige



Implicancia:

El sistema no debe limitarse al sueldo mensual. Debe preparar la arquitectura para beneficios sociales, liquidaciones y provisiones.

## 4. Conceptos remunerativos y no remunerativos



Requisito funcional:

El sistema debe manejar conceptos configurables.



Cada concepto debe tener:

\- Código interno

\- Nombre

\- Tipo: ingreso, descuento, aporte trabajador, aporte empleador

\- Si es remunerativo o no remunerativo

\- Si afecta CTS

\- Si afecta gratificación

\- Si afecta vacaciones

\- Si afecta EsSalud

\- Si afecta renta de quinta

\- Si afecta AFP/ONP

\- Vigencia desde / hasta

\- Fórmula o regla de cálculo

\- Estado activo/inactivo



Regla:

No crear conceptos de planilla como columnas sueltas ni fórmulas rígidas.

