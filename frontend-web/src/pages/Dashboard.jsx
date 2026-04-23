import { useState, useEffect } from 'react';
import {
  Download,
  Clock,
  Users,
  CalendarDays,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  ShieldCheck,
  RotateCw,
  Building2,
  UserX,
} from 'lucide-react';
import { getAdminStats, getAdminAttendance, downloadAttendanceReport, processTimesheets } from '../services/api';
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
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsRes, attendanceRes] = await Promise.all([
        getAdminStats(),
        getAdminAttendance(),
      ]);
      setStats(statsRes.data);
      setRecords(attendanceRes.data);
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
      await downloadAttendanceReport();
    } catch (err) {
      console.error('Error exporting CSV:', err);
      alert('Error al exportar el reporte');
    }
  };

  const handleProcessTimesheets = async () => {
    if (!window.confirm('¿Deseas procesar todas las jornadas de los últimos 7 días? Este proceso consolidará las horas extra y tardanzas.')) return;

    try {
      setProcessing(true);
      await processTimesheets({});
      alert('Cierre de planilla completado con éxito. Iniciando descarga de reporte consolidado...');
      await handleExport();
    } catch (err) {
      console.error('Error processing timesheets:', err);
      alert('Error al procesar el cierre de planilla');
    } finally {
      setProcessing(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh cada 30 segundos
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
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
          {(loading || processing) && <RotateCw className="animate-spin text-gold" size={20} />}
          <button 
            className="btn-process-wfm" 
            onClick={handleProcessTimesheets}
            disabled={processing}
          >
            <Clock size={18} />
            {processing ? 'Procesando...' : 'Cierre de Planilla'}
          </button>
          <button className="btn-export" onClick={handleExport}>
            <Download size={18} />
            Exportar CSV
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
                      <span className={`badge ${r.action === 'check_in' ? 'badge-success' : 'badge-warning'}`}>
                        {r.action === 'check_in' ? (
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
