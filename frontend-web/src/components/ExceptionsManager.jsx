import { useState } from 'react';
import { AlertCircle, Clock, CheckCircle, TimerReset } from 'lucide-react';
import { resolveException } from '../services/api';
import './ExceptionsManager.css';

const MOCK_EXCEPTIONS = [
  {
    id: 101,
    employee: 'Ricardo Espinal',
    date: '2026-04-20',
    scheludedTime: '08:00 - 17:00',
    actualTime: '08:02 - 19:15',
    excess: '+2h 15m',
    reason: 'Cierre de inventario trimestral',
  },
  {
    id: 102,
    employee: 'Sofía Méndez',
    date: '2026-04-20',
    scheludedTime: '09:00 - 18:00',
    actualTime: '08:45 - 19:30',
    excess: '+1h 30m',
    reason: 'Soporte técnico extendido',
  }
];

export default function ExceptionsManager() {
  const [exceptions, setExceptions] = useState(MOCK_EXCEPTIONS);

  const handleResolve = async (id, type) => {
    try {
      await resolveException(id, type);
      // Simulación: eliminamos de la lista al resolver
      setExceptions(prev => prev.filter(ex => ex.id !== id));
    } catch (err) {
      // Ignoramos error en simulación ya que el endpoint no existe
      setExceptions(prev => prev.filter(ex => ex.id !== id));
    }
  };

  return (
    <div className="exceptions-section">
      <div className="table-header">
        <div className="table-title-row">
          <AlertCircle size={20} className="text-warning" />
          <h2 className="table-title">Incidencias por Resolver</h2>
        </div>
        <span className="badge badge-warning">{exceptions.length} Pendientes</span>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Empleado</th>
              <th>Fecha</th>
              <th>Turno Teórico</th>
              <th>Turno Real</th>
              <th>Tiempo Excedente</th>
              <th style={{ textAlign: 'right' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {exceptions.length > 0 ? (
              exceptions.map((ex) => (
                <tr key={ex.id}>
                  <td className="cell-name">{ex.employee}</td>
                  <td>{ex.date}</td>
                  <td>{ex.scheludedTime}</td>
                  <td>{ex.actualTime}</td>
                  <td className="cell-hours text-danger">{ex.excess}</td>
                  <td className="cell-actions">
                    <div className="action-group">
                      <button 
                        className="btn-action btn-extra"
                        onClick={() => handleResolve(ex.id, 'overtime')}
                        title="Aprobar como Hora Extra"
                      >
                        <CheckCircle size={14} />
                        Horas Extra
                      </button>
                      <button 
                        className="btn-action btn-compensate"
                        onClick={() => handleResolve(ex.id, 'compensate')}
                        title="Compensar Tiempo"
                      >
                        <TimerReset size={14} />
                        Compensar
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--color-text-secondary)' }}>
                  No hay incidencias de tiempo pendientes de resolución.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
