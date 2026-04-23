from utils.db import query_one, query_all, tx
from services.timesheet_engine import process_timesheet
import sys

def reprocess_period(period_id):
    # 1. Obtener detalles del periodo
    period = query_one("SELECT starts_on, ends_on, state FROM payroll_periods WHERE id = %s", (period_id,))
    if not period:
        print(f"Error: Periodo {period_id} no existe.")
        return
    
    if period['state'] == 'closed':
        print(f"Error: El periodo {period_id} está CERRADO. No se puede reprocesar.")
        return

    print(f"Reprocesando periodo {period_id} ({period['starts_on']} a {period['ends_on']})...")

    # 2. Obtener todos los empleados que tienen marcaciones o deberían tenerlas en ese rango
    # Para simplificar, obtenemos todos los empleados activos
    employees = query_all("SELECT id, name FROM employees WHERE is_active = True")
    
    total_days = (period['ends_on'] - period['starts_on']).days + 1
    
    for emp in employees:
        print(f"  Procesando empleado: {emp['name']}...")
        for i in range(total_days):
            current_date = period['starts_on'] + timedelta(days=i)
            process_timesheet(emp['id'], current_date)
            
    print("Reproceso completado.")

if __name__ == "__main__":
    from datetime import timedelta
    if len(sys.argv) < 2:
        print("Uso: python reprocess_period.py <period_id>")
    else:
        reprocess_period(sys.argv[1])
