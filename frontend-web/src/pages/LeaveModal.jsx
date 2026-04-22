import React, { useState } from 'react';
import { X, Calendar, Briefcase, Heart, User, CheckCircle } from 'lucide-react';
import { createLeave } from '../services/api';

const LeaveModal = ({ employee, onClose }) => {
  const [formData, setFormData] = useState({
    logical_date: new Date().toISOString().split('T')[0],
    leave_type: 'Vacaciones',
    is_paid: true
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await createLeave({
        employee_id: employee.id,
        ...formData
      });
      alert('Permiso registrado y jornada actualizada.');
      onClose();
    } catch (err) {
      console.error('Error creating leave:', err);
      alert('Error al registrar el permiso.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content premium-card">
        <header className="modal-header">
          <div className="modal-title-row">
            <div className="modal-icon-container">
              <Briefcase className="text-gold" size={24} />
            </div>
            <div>
              <h2 className="modal-title">Registrar Permiso</h2>
              <p className="modal-subtitle">{employee.full_name}</p>
            </div>
          </div>
          <button className="btn-close" onClick={onClose}>
            <X size={20} />
          </button>
        </header>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label>Fecha del Permiso</label>
            <div className="input-with-icon">
              <Calendar size={18} />
              <input 
                type="date" 
                required 
                value={formData.logical_date}
                onChange={(e) => setFormData({...formData, logical_date: e.target.value})}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Tipo de Permiso</label>
            <div className="input-with-icon">
              <Heart size={18} />
              <select 
                value={formData.leave_type}
                onChange={(e) => setFormData({...formData, leave_type: e.target.value})}
              >
                <option value="Vacaciones">Vacaciones</option>
                <option value="Salud">Salud / Médica</option>
                <option value="Personal">Asuntos Personales</option>
                <option value="Capacitación">Capacitación</option>
              </select>
            </div>
          </div>

          <div className="form-group-checkbox">
            <label className="checkbox-container">
              <input 
                type="checkbox" 
                checked={formData.is_paid}
                onChange={(e) => setFormData({...formData, is_paid: e.target.checked})}
              />
              <span className="checkmark"></span>
              Es Remunerado
            </label>
            <p className="field-hint">Si es remunerado, no se descontará del sueldo base.</p>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={loading}>
              Cancelar
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Guardando...' : 'Registrar Permiso'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LeaveModal;
