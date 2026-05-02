import React, { useState } from 'react';
import { X, Save, AlertCircle } from 'lucide-react';
import './WfmManager.css';

const ResolveModal = ({ issue, onClose, onResolve }) => {
  const isOrphanIn = issue.anomaly_flags?.includes('orphan_in');
  const isOrphanOut = issue.anomaly_flags?.includes('orphan_out');
  const [action, setAction] = useState(() => (isOrphanOut ? 'manual_in' : 'manual_out'));
  const [time, setTime] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    await onResolve(issue.id, { action, time, reason });
    setLoading(false);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content resolve-modal">
        <div className="modal-header">
          <h3>Resolver Anomalía</h3>
          <button onClick={onClose} className="close-btn"><X size={20} /></button>
        </div>

        <div className="modal-body">
          <div className="issue-summary">
            <p><strong>Empleado:</strong> {issue.full_name}</p>
            <p><strong>Fecha:</strong> {issue.logical_date}</p>
            <div className="alert-box">
              <AlertCircle size={18} />
              <span>
                {isOrphanIn && "Falta marcación de salida. El empleado entró pero no hay registro de salida."}
                {isOrphanOut && "Falta marcación de entrada. Hay una salida sin entrada previa."}
                {!isOrphanIn && !isOrphanOut && "Revisión manual requerida por horas extra o inconsistencias."}
              </span>
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Acción Correctiva</label>
              <select 
                value={action} 
                onChange={(e) => setAction(e.target.value)}
                required
              >
                <option value="manual_in">Insertar Entrada Manual</option>
                <option value="manual_out">Insertar Salida Manual</option>
              </select>
            </div>

            <div className="form-group">
              <label>Hora de Marcación (HH:MM)</label>
              <input 
                type="time" 
                value={time} 
                onChange={(e) => setTime(e.target.value)} 
                required 
              />
            </div>

            <div className="form-group">
              <label>Justificación / Motivo</label>
              <textarea 
                placeholder="Ej: Olvido marcar al salir, falla de equipo..."
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                required
              ></textarea>
            </div>

            <div className="modal-footer">
              <button type="button" onClick={onClose} className="secondary-btn">Cancelar</button>
              <button type="submit" className="primary-btn" disabled={loading}>
                <Save size={18} />
                {loading ? 'Procesando...' : 'Aplicar y Recalcular'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ResolveModal;
