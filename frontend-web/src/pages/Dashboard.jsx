import { useState, useEffect } from 'react';
import {
  Clock,
  Users,
  CalendarDays,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  ShieldCheck,
  Lock,
  Unlock,
  FileText,
  RotateCw,
  Building2,
  UserX,
  PlayCircle,
} from 'lucide-react';
import { 
  getAdminStats, 
  getAdminAttendance, 
  downloadAttendanceReport, 
  processTimesheets,
  getPayrollPeriods,
  closePayrollPeriod,
  getWfmIssues,
} from '../services/api';
import ExceptionsManager from '../components/ExceptionsManager';
import './Dashboard.css';

export default function Dashboard() {
  const [records, setRecords] = useState([]);
  const [stats, setStats] = useState({
    active_employees: 0,
    present_today: 0,
    total_buildings: 0,
    avg_punctuality: 0,
  });
  const [periods, setPeriods] = useState([]);
  const [selectedPeriodId, setSelectedPeriodId] = useState('');
  const [wfmIssueCount, setWfmIssueCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsRes, attendanceRes, periodsRes, wfmRes] = await Promise.all([
        getAdminStats(),
        getAdminAttendance(),
        getPayrollPeriods(),
        getWfmIssues(),
      ]);
      setStats(statsRes.data);
      setRecords(attendanceRes.data);
      setPeriods(periodsRes.data);
      setWfmIssueCount(wfmRes.data.length);
      
      // Auto-seleccionar el primer periodo abierto si no hay seleccion
      if (!selectedPeriodId && periodsRes.data.length > 0) {
        const active = periodsRes.data.find(p => p.state === 'open') || periodsRes.data[0];
        setSelectedPeriodId(active.id);
      }
      
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('No se pudo conectar con el servidor. Verifica que el backend esté corriendo.');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      await downloadAttendanceReport(selectedPeriodId);
    } catch (err) {
      console.error('Error exporting CSV:', err);
      alert('Error al exportar el reporte');
    }
  };

  const handleClosePeriod = async () => {
    const period = periods.find(p => p.id === selectedPeriodId);
    if (!period || period.state === 'closed') return;

    if (!window.confirm(`¿Estás seguro de CERRAR DEFINITIVAMENTE el periodo "${period.name}"? Esto bloqueará todos los registros y no podrán ser modificados.`)) return;

    try {
      setProcessing(true);
      await closePayrollPeriod(selectedPeriodId);
      alert('Periodo cerrado y bloqueado con éxito.');
      fetchData();
    } catch (err) {
      console.error('Error closing period:', err);
      alert('Error al cerrar el periodo');
    } finally {
      setProcessing(false);
    }
  };

  const handleProcessTimesheets = async () => {
    if (!window.confirm('¿Deseas procesar todas las jornadas? Este proceso consolidará las horas extra y tardanzas para el periodo seleccionado.')) return;

    try {
      setProcessing(true);
      await processTimesheets({ period_id: selectedPeriodId });
      alert('Procesamiento completado con éxito.');
      fetchData();
    } catch (err) {
      console.error('Error processing timesheets:', err);
      alert('Error al procesar las jornadas');
    } finally {
      setProcessing(false);
    }
  };

  useEffect(() => {
    let cancelled = false;

    const refreshDashboard = async () => {
      try {
      const [statsRes, attendanceRes, periodsRes, wfmRes] = await Promise.all([
          getAdminStats(),
          getAdminAttendance(),
          getPayrollPeriods(),
          getWfmIssues(),
        ]);

        if (cancelled) return;

        setStats(statsRes.data);
        setRecords(attendanceRes.data);
        setPeriods(periodsRes.data);
        setWfmIssueCount(wfmRes.data.length);

        if (periodsRes.data.length > 0) {
          const active = periodsRes.data.find(p => p.state === 'open') || periodsRes.data[0];
          setSelectedPeriodId(current => current || active.id);
        }

        setError(null);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        if (!cancelled) {
          setError('No se pudo conectar con el servidor. Verifica que el backend estÃ© corriendo.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    refreshDashboard();
    const interval = setInterval(refreshDashboard, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const formatDate = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('es-HN');
  };

  const formatTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('es-HN', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  if (error) {
    return (
      <div className="dashboard-error">
        <AlertTriangle size={48} />
        <h2>Error de Conexión</h2>
        <p>{error}</p>
        <button onClick={fetchData} className="btn-retry">
          <RotateCw size={18} /> Reintentar
        </button>
      </div>
    );
  }

  const selectedPeriod = periods.find(p => p.id === selectedPeriodId);
  const hasBlockingWfmIssues = wfmIssueCount > 0;
  const closePeriodDisabled =
    processing || selectedPeriod?.state === 'closed' || hasBlockingWfmIssues;

  return (
    <div className="dashboard">
      {/* ── Header ── */}
      <header className="dashboard-header">
        <div className="header-left">
          <img src="/logo-trans.png" alt="Grupo Hernández" className="header-logo" />
          <div>
            <h1 className="header-title">Panel de Asistencia</h1>
            <p className="header-subtitle">Grupo Hernández · Recursos Humanos</p>
          </div>
        </div>
        <div className="header-actions">
          {(loading || processing) && <div className="spinner-small" />}
          
          <div className="period-selector-container">
            <CalendarDays size={18} className="text-gold" />
            <select 
              value={selectedPeriodId} 
              onChange={(e) => setSelectedPeriodId(e.target.value)}
              className="period-select"
            >
              {periods.map(p => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.state === 'open' ? 'Abierto' : 'Cerrado'})
                </option>
              ))}
              {periods.length === 0 && <option>No hay periodos creados</option>}
            </select>
          </div>

          <button 
            className={`btn-lock ${selectedPeriod?.state === 'closed' ? 'locked' : ''}`}
            onClick={handleClosePeriod}
            disabled={closePeriodDisabled}
            title={hasBlockingWfmIssues ? `${wfmIssueCount} incidencia(s) WFM pendiente(s)` : undefined}
          >
            {selectedPeriod?.state === 'closed' ? (
              <><Lock size={18} /> Periodo Cerrado</>
            ) : hasBlockingWfmIssues ? (
              <><AlertTriangle size={18} /> Resolver Incidencias</>
            ) : (
              <><Unlock size={18} /> Cerrar Periodo</>
            )}
          </button>

          <button
            className="btn-export"
            onClick={handleProcessTimesheets}
            disabled={processing || !selectedPeriodId}
          >
            <PlayCircle size={18} />
            Procesar Jornadas
          </button>

          <button className="btn-export" onClick={handleExport}>
            <FileText size={18} />
            Descargar CSV
          </button>
        </div>
      </header>

      {/* ── Summary Cards ── */}
      <section className="summary-grid">
        <div className="summary-card">
          <div className="summary-icon" style={{ background: 'var(--color-gold-light)', color: 'var(--color-gold)' }}>
            <Users size={22} />
          </div>
          <div className="summary-info">
            <span className="summary-value">{stats.active_employees}</span>
            <span className="summary-label">Empleados Activos</span>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon" style={{ background: 'var(--color-success-bg)', color: 'var(--color-success)' }}>
            <CheckCircle2 size={22} />
          </div>
          <div className="summary-info">
            <span className="summary-value">{stats.present_today}</span>
            <span className="summary-label">Presentes Hoy</span>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon" style={{ background: 'rgba(99,102,241,0.1)', color: '#6366f1' }}>
            <Building2 size={22} />
          </div>
          <div className="summary-info">
            <span className="summary-value">{stats.total_buildings}</span>
            <span className="summary-label">Sedes Operativas</span>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon" style={{ background: 'var(--color-gold-light)', color: 'var(--color-gold)' }}>
            <TrendingUp size={22} />
          </div>
          <div className="summary-info">
            <span className="summary-value">{stats.avg_punctuality}%</span>
            <span className="summary-label">Puntualidad Global</span>
          </div>
        </div>
      </section>

      {/* ── WFM Exceptions Module ── */}
      <ExceptionsManager />

      {/* ── Table ── */}
      <section className="table-section" style={{ marginTop: '32px' }}>
        <div className="table-header">
          <div className="table-title-row">
            <CalendarDays size={20} />
            <h2 className="table-title">Última Actividad (Tiempo Real)</h2>
          </div>
          <span className="table-date">
            {new Date().toLocaleDateString('es-HN', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </span>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Empleado</th>
                <th>Sede / Edificio</th>
                <th>Acción</th>
                <th>Fecha</th>
                <th>Hora</th>
                <th>Método</th>
                <th>Biometría</th>
              </tr>
            </thead>
            <tbody>
              {records.length > 0 ? (
                records.map((r) => (
                  <tr key={r.id}>
                    <td className="cell-name">{r.employee}</td>
                    <td>{r.building}</td>
                    <td>
                      <span className={`badge ${r.action === 'in' ? 'badge-success' : 'badge-warning'}`}>
                        {r.action === 'in' ? (
                          <><CheckCircle2 size={13} /> Entrada</>
                        ) : (
                          <><Clock size={13} /> Salida</>
                        )}
                      </span>
                    </td>
                    <td>{formatDate(r.time)}</td>
                    <td className="cell-hours">{formatTime(r.time)}</td>
                    <td>
                      <span className="badge badge-neutral">
                        {r.method}
                      </span>
                    </td>
                    <td>
                      {r.method !== 'Manual' ? (
                        <div className={`biometric-status ${
                          r.biometric_status === 'passed' ? 'text-success' : 
                          r.biometric_status === 'unavailable' ? 'text-warning' : 'text-danger'
                        }`}>
                          {r.biometric_status === 'passed' ? (
                            <><ShieldCheck size={14} /> Verificado</>
                          ) : r.biometric_status === 'unavailable' ? (
                            <><AlertTriangle size={14} /> N/D (Offline)</>
                          ) : r.biometric_status === 'failed' ? (
                            <><UserX size={14} /> No Coincide</>
                          ) : (
                            <><Clock size={14} /> {r.biometric_status}</>
                          )}
                        </div>
                      ) : (
                        <div className="biometric-status text-muted">
                          <UserX size={14} /> Manual / N/D
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>
                    No hay registros de asistencia para mostrar hoy.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
