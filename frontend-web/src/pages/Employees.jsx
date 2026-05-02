import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Plus, 
  Search,
  X,
  User,
  Briefcase,
  Building,
  ShieldAlert,
  CalendarClock,
  UserPlus,
  Building2,
  DollarSign,
  Heart
} from 'lucide-react';
import { getEmployees, createEmployee, getBuildings, getRoles } from '../services/api';
import ScheduleModal from './ScheduleModal';
import LeaveModal from './LeaveModal';
import './Employees.css';

const Employees = () => {
  const [employees, setEmployees] = useState([]);
  const [buildings, setBuildings] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [formData, setFormData] = useState({ 
    full_name: '', 
    job_title: '', 
    primary_building_id: '',
    role_id: '',
    hourly_wage: 0
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [empRes, buildRes, roleRes] = await Promise.all([
        getEmployees(),
        getBuildings(),
        getRoles()
      ]);
      setEmployees(empRes.data);
      setBuildings(buildRes.data);
      setRoles(roleRes.data);
      
      if (roleRes.data.length > 0) {
        const workerRole = roleRes.data.find(r => r.name.toLowerCase() === 'worker');
        setFormData(prev => ({...prev, role_id: workerRole ? workerRole.id : roleRes.data[0].id}));
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.full_name) return;

    setIsSubmitting(true);
    try {
      await createEmployee(formData);
      setShowModal(false);
      setFormData({ 
        full_name: '', 
        job_title: '', 
        primary_building_id: buildings[0]?.id || '',
        role_id: roles.find(r => r.name.toLowerCase() === 'worker')?.id || roles[0]?.id || '',
        hourly_wage: 0
      });
      fetchData();
    } catch (error) {
      console.error('Error creating employee:', error);
      alert('Error al crear el empleado');
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    let cancelled = false;

    const loadInitialData = async () => {
      try {
        const [empRes, buildRes, roleRes] = await Promise.all([
          getEmployees(),
          getBuildings(),
          getRoles()
        ]);

        if (cancelled) return;

        setEmployees(empRes.data);
        setBuildings(buildRes.data);
        setRoles(roleRes.data);

        if (roleRes.data.length > 0) {
          const workerRole = roleRes.data.find(r => r.name.toLowerCase() === 'worker');
          setFormData(prev => ({...prev, role_id: workerRole ? workerRole.id : roleRes.data[0].id}));
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadInitialData();

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredEmployees = employees.filter(e => 
    e.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.job_title?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="employees-container">
      <header className="view-header">
        <div className="header-left">
          <h1>Gestión de Empleados</h1>
          <p>Catálogo de personal y asignación de sedes</p>
        </div>
        <button className="add-btn" onClick={() => setShowModal(true)}>
          <Plus size={20} />
          <span>Nuevo Empleado</span>
        </button>
      </header>

      <div className="search-bar">
        <Search size={20} color="#6c757d" />
        <input 
          type="text" 
          placeholder="Buscar empleado por nombre o cargo..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="content-card">
        {loading ? (
          <div className="loading-state">Cargando personal...</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Empleado</th>
                <th>Cargo</th>
                <th>Sede Principal</th>
                <th>Rol</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredEmployees.length > 0 ? (
                filteredEmployees.map((employee) => (
                  <tr key={employee.id}>
                    <td>
                      <div className="employee-info">
                        <User size={18} color="#001a33" />
                        <span>{employee.full_name}</span>
                      </div>
                    </td>
                    <td>
                      <div className="job-info">
                        <Briefcase size={16} color="#6c757d" />
                        <span>{employee.job_title || 'N/A'}</span>
                      </div>
                    </td>
                    <td>
                      <div className="building-info-tag">
                        <Building size={16} color="#D4AF37" />
                        <span>{employee.building_name || 'Sin Sede'}</span>
                      </div>
                    </td>
                    <td>
                       <span className="role-tag">{employee.role_name}</span>
                    </td>
                    <td>
                      <span className={`status-pill ${employee.status}`}>
                        {employee.status === 'active' ? 'Activo' : employee.status}
                      </span>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button 
                          className="action-btn schedule" 
                          title="Horarios"
                          onClick={() => {
                            setSelectedEmployee(employee);
                            setShowScheduleModal(true);
                          }}
                        >
                          <CalendarClock size={16} />
                        </button>
                        <button 
                          className="action-btn leave" 
                          title="Registrar Permiso"
                          onClick={() => {
                            setSelectedEmployee(employee);
                            setShowLeaveModal(true);
                          }}
                        >
                          <Heart size={16} />
                        </button>
                        <button className="text-btn">Expediente</button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '40px' }}>
                    No se encontraron empleados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2>Registrar Nuevo Empleado</h2>
              <button className="close-btn" onClick={() => setShowModal(false)}>
                <X size={24} />
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Nombre Completo</label>
                <input 
                  type="text" 
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  placeholder="Ej: Juan Pérez..."
                  required
                />
              </div>
              <div className="form-group">
                <label>Cargo / Puesto</label>
                <input 
                  type="text" 
                  value={formData.job_title}
                  onChange={(e) => setFormData({...formData, job_title: e.target.value})}
                  placeholder="Ej: Operario de Almacén..."
                />
              </div>
              <div className="form-group">
                <label>Sede Primaria</label>
                <div className="input-with-icon">
                  <Building2 size={18} />
                  <select 
                    required 
                    value={formData.primary_building_id}
                    onChange={(e) => setFormData({...formData, primary_building_id: e.target.value})}
                  >
                    <option value="">Seleccionar Sede</option>
                    {buildings.map(b => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Tarifa por Hora (S/)</label>
                <div className="input-with-icon">
                  <DollarSign size={18} />
                  <input 
                    type="number" 
                    step="0.10"
                    min="0"
                    placeholder="Ej. 15.50"
                    value={formData.hourly_wage}
                    onChange={(e) => setFormData({...formData, hourly_wage: e.target.value})}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Rol de Sistema</label>
                <select 
                  value={formData.role_id}
                  onChange={(e) => setFormData({...formData, role_id: e.target.value})}
                  required
                >
                  {roles.map(r => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                </select>
              </div>
              <div className="modal-footer">
                <button type="button" className="cancel-btn" onClick={() => setShowModal(false)}>
                  Cancelar
                </button>
                <button type="submit" className="submit-btn" disabled={isSubmitting}>
                  {isSubmitting ? 'Registrando...' : 'Registrar Empleado'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showScheduleModal && selectedEmployee && (
        <ScheduleModal 
          employee={selectedEmployee} 
          onClose={() => setShowScheduleModal(false)} 
        />
      )}

      {showLeaveModal && selectedEmployee && (
        <LeaveModal 
          employee={selectedEmployee} 
          onClose={() => setShowLeaveModal(false)} 
        />
      )}
    </div>
  );
};

export default Employees;
