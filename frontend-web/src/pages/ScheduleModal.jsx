import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { getEmployeeSchedule, updateEmployeeSchedule, getBuildings } from '../services/api';
import './ScheduleModal.css';

const DAYS_ES = [
  'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'
];

const ScheduleModal = ({ isOpen = true, onClose, employee }) => {
  const [schedule, setSchedule] = useState([]);
  const [buildings, setBuildings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isOpen || !employee) return;

    let cancelled = false;

    const loadData = async () => {
      try {
        const [schedRes, buildRes] = await Promise.all([
          getEmployeeSchedule(employee.id),
          getBuildings()
        ]);

        if (cancelled) return;

        setBuildings(buildRes.data);

        const fullSchedule = DAYS_ES.map((name, index) => {
          const existing = schedRes.data.find(s => s.day_of_week === index);
          return {
            day_of_week: index,
            day_name: name,
            active: !!existing,
            start_time: existing?.start_time || '08:00',
            end_time: existing?.end_time || '17:00',
            building_id: existing?.building_id || employee.primary_building_id || buildRes.data[0]?.id || '',
            is_overnight: existing?.is_overnight || false,
            tolerance_minutes: existing?.tolerance_minutes || 15
          };
        });

        setSchedule(fullSchedule);
      } catch (error) {
        console.error('Error loading schedule:', error);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadData();

    return () => {
      cancelled = true;
    };
  }, [isOpen, employee]);

  const handleToggle = (index) => {
    const newSchedule = [...schedule];
    newSchedule[index].active = !newSchedule[index].active;
    setSchedule(newSchedule);
  };

  const handleChange = (index, field, value) => {
    const newSchedule = [...schedule];
    newSchedule[index][field] = value;
    setSchedule(newSchedule);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateEmployeeSchedule(employee.id, schedule);
      onClose();
    } catch (error) {
      console.error('Error saving schedule:', error);
      alert('Error al guardar el horario');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="schedule-modal-overlay">
      <div className="schedule-modal">
        <header className="schedule-modal-header">
          <div className="modal-branding">
            <img src="/logo-trans.png" alt="Grupo Hernández" className="corporate-logo-small" />
            <div className="header-text">
              <h2>Horario Semanal</h2>
              <p>{employee?.full_name} - Asignación de Turnos</p>
            </div>
          </div>
          <button className="close-btn-white" onClick={onClose}>
            <X size={24} />
          </button>
        </header>

        <div className="schedule-modal-body">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>Cargando configuración...</div>
          ) : (
            <div className="days-grid">
              {schedule.map((day, index) => (
                <div key={day.day_of_week} className={`day-row ${day.active ? 'active' : ''}`}>
                  <span className="day-name">{day.day_name}</span>

                  <label className="switch">
                    <input
                      type="checkbox"
                      checked={day.active}
                      onChange={() => handleToggle(index)}
                    />
                    <span className="slider"></span>
                  </label>

                  <div className="time-input-group">
                    <label>Entrada</label>
                    <input
                      type="time"
                      disabled={!day.active}
                      value={day.start_time}
                      onChange={(e) => handleChange(index, 'start_time', e.target.value)}
                    />
                  </div>

                  <div className="time-input-group">
                    <label>Salida</label>
                    <input
                      type="time"
                      disabled={!day.active}
                      value={day.end_time}
                      onChange={(e) => handleChange(index, 'end_time', e.target.value)}
                    />
                  </div>

                  <div className="time-input-group">
                    <label>Sede de Trabajo</label>
                    <select
                      disabled={!day.active}
                      value={day.building_id}
                      onChange={(e) => handleChange(index, 'building_id', e.target.value)}
                    >
                      {buildings.map(b => (
                        <option key={b.id} value={b.id}>{b.name}</option>
                      ))}
                    </select>
                  </div>

                  <label className="overnight-check">
                    <input
                      type="checkbox"
                      disabled={!day.active}
                      checked={day.is_overnight}
                      onChange={(e) => handleChange(index, 'is_overnight', e.target.checked)}
                    />
                    <span>Amanecida</span>
                  </label>
                </div>
              ))}
            </div>
          )}
        </div>

        <footer className="schedule-modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancelar</button>
          <button
            className="btn-primary"
            onClick={handleSave}
            disabled={saving || loading}
          >
            {saving ? 'Guardando...' : 'Guardar Horario'}
          </button>
        </footer>
      </div>
    </div>
  );
};

export default ScheduleModal;
