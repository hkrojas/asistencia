import { useState } from 'react';
import {
  Download,
  Clock,
  Users,
  CalendarDays,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
} from 'lucide-react';
import './Dashboard.css';

/* ── Datos mock ── */
const MOCK_RECORDS = [
  {
    id: 1,
    name: 'Juan Pérez',
    date: '20/04/2026',
    checkIn: '07:58 AM',
    checkOut: '05:02 PM',
    hours: '9h 04m',
    status: 'puntual',
  },
  {
    id: 2,
    name: 'María López',
    date: '20/04/2026',
    checkIn: '08:23 AM',
    checkOut: '05:15 PM',
    hours: '8h 52m',
    status: 'tardanza',
  },
  {
    id: 3,
    name: 'Carlos Rivera',
    date: '20/04/2026',
    checkIn: '07:45 AM',
    checkOut: '04:50 PM',
    hours: '9h 05m',
    status: 'puntual',
  },
];

const MOCK_SUMMARY = {
  totalEmployees: 24,
  presentToday: 21,
  lateToday: 3,
  avgHours: '8h 42m',
};

export default function Dashboard() {
  const [records] = useState(MOCK_RECORDS);
  const summary = MOCK_SUMMARY;

  return (
    <div className="dashboard">
      {/* ── Header ── */}
      <header className="dashboard-header">
        <div className="header-left">
          <img src="/logo.png" alt="Grupo Hernández" className="header-logo" />
          <div>
            <h1 className="header-title">Panel de Asistencia</h1>
            <p className="header-subtitle">Grupo Hernández · Recursos Humanos</p>
          </div>
        </div>
        <button className="btn-export" onClick={() => alert('Exportar — Próximamente')}>
          <Download size={18} />
          Exportar a CSV
        </button>
      </header>

      {/* ── Summary Cards ── */}
      <section className="summary-grid">
        <div className="summary-card">
          <div className="summary-icon" style={{ background: 'var(--color-gold-light)', color: 'var(--color-gold)' }}>
            <Users size={22} />
          </div>
          <div className="summary-info">
            <span className="summary-value">{summary.totalEmployees}</span>
            <span className="summary-label">Empleados</span>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon" style={{ background: 'var(--color-success-bg)', color: 'var(--color-success)' }}>
            <CheckCircle2 size={22} />
          </div>
          <div className="summary-info">
            <span className="summary-value">{summary.presentToday}</span>
            <span className="summary-label">Presentes Hoy</span>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon" style={{ background: 'var(--color-warning-bg)', color: 'var(--color-warning)' }}>
            <AlertTriangle size={22} />
          </div>
          <div className="summary-info">
            <span className="summary-value">{summary.lateToday}</span>
            <span className="summary-label">Tardanzas</span>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon" style={{ background: 'rgba(99,102,241,0.1)', color: '#6366f1' }}>
            <TrendingUp size={22} />
          </div>
          <div className="summary-info">
            <span className="summary-value">{summary.avgHours}</span>
            <span className="summary-label">Promedio Horas</span>
          </div>
        </div>
      </section>

      {/* ── Table ── */}
      <section className="table-section">
        <div className="table-header">
          <div className="table-title-row">
            <CalendarDays size={20} />
            <h2 className="table-title">Registros del Día</h2>
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
                <th>Fecha</th>
                <th>
                  <Clock size={14} className="th-icon" />
                  Ingreso
                </th>
                <th>
                  <Clock size={14} className="th-icon" />
                  Salida
                </th>
                <th>Horas Efectivas</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id}>
                  <td className="cell-name">{r.name}</td>
                  <td>{r.date}</td>
                  <td>{r.checkIn}</td>
                  <td>{r.checkOut}</td>
                  <td className="cell-hours">{r.hours}</td>
                  <td>
                    <span className={`badge ${r.status === 'puntual' ? 'badge-success' : 'badge-warning'}`}>
                      {r.status === 'puntual' ? (
                        <><CheckCircle2 size={13} /> Puntual</>
                      ) : (
                        <><AlertTriangle size={13} /> Tardanza</>
                      )}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
