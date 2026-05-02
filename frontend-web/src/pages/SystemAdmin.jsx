import React, { useEffect, useState } from 'react';
import { getAuditEvents } from '../services/api';
import './WorkflowPages.css';

export default function SystemAdmin() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    getAuditEvents()
      .then(({ data }) => setEvents(data))
      .catch(() => setEvents([]));
  }, []);

  return (
    <div className="workflow-page">
      <header className="workflow-header">
        <div>
          <h1>Administracion</h1>
          <p>Auditoria transversal de cambios sensibles y configuracion operativa.</p>
        </div>
      </header>

      {events.length === 0 ? (
        <div className="workflow-empty">Aun no hay eventos de auditoria registrados.</div>
      ) : (
        <table className="workflow-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Modulo</th>
              <th>Accion</th>
              <th>Entidad</th>
              <th>Motivo</th>
            </tr>
          </thead>
          <tbody>
            {events.map(event => (
              <tr key={event.id}>
                <td>{new Date(event.created_at).toLocaleString()}</td>
                <td>{event.module}</td>
                <td>{event.action}</td>
                <td>{event.entity_type}</td>
                <td>{event.reason || 'Sin motivo'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

