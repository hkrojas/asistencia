import { useState, useEffect } from 'react';
import { AlertCircle, Clock, CheckCircle, TimerReset, Loader2 } from 'lucide-react';
import { resolveException, getPendingExceptions } from '../services/api';
import './ExceptionsManager.css';

export default function ExceptionsManager() {
  const [exceptions, setExceptions] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchExceptions = async () => {
    try {
      const { data } = await getPendingExceptions();
      setExceptions(data);
    } catch (err) {
      console.error('Error fetching exceptions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExceptions();
    // Auto-refresh cada 60 segundos para incidencias nuevas
    const interval = setInterval(fetchExceptions, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleResolve = async (id, type) => {
    try {
      await resolveException(id, type);
      // Removemos de la lista localmente tras éxito
      setExceptions(prev => prev.filter(ex => ex.id !== id));
    } catch (err) {
      console.error('Error resolving exception:', err);
      alert('Error al procesar la resolución');
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
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
            <Loader2 className="animate-spin" size={32} />
          </div>
        ) : (
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
        )}
      </div>
    </div>
  );
}
