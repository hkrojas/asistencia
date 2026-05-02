import React, { useEffect, useState } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { getOperationsDashboard, getPayrollPeriods } from '../services/api';
import './WorkflowPages.css';

export default function Operations() {
  const [periods, setPeriods] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('');
  const [buildings, setBuildings] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = async (periodId = selectedPeriod) => {
    setLoading(true);
    try {
      const [periodsRes, dashboardRes] = await Promise.all([
        getPayrollPeriods(),
        getOperationsDashboard(periodId),
      ]);
      setPeriods(periodsRes.data);
      if (!periodId && periodsRes.data.length > 0) {
        const active = periodsRes.data.find(p => p.state === 'open') || periodsRes.data[0];
        setSelectedPeriod(active.id);
      }
      setBuildings(dashboardRes.data.buildings || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    async function loadInitialData() {
      const [periodsRes, dashboardRes] = await Promise.all([
        getPayrollPeriods(),
        getOperationsDashboard(''),
      ]);
      if (cancelled) return;
      setPeriods(periodsRes.data);
      if (periodsRes.data.length > 0) {
        const active = periodsRes.data.find(p => p.state === 'open') || periodsRes.data[0];
        setSelectedPeriod(active.id);
      }
      setBuildings(dashboardRes.data.buildings || []);
      setLoading(false);
    }
    loadInitialData().catch(() => {
      if (!cancelled) setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const totals = buildings.reduce((acc, building) => {
    acc.workers += Number(building.active_workers || 0);
    acc.pending += Number(building.pending_coverages || 0);
    acc.prepayrolls += Number(building.prepayroll_count || 0);
    return acc;
  }, { workers: 0, pending: 0, prepayrolls: 0 });

  return (
    <div className="workflow-page">
      <header className="workflow-header">
        <div>
          <h1>Operacion por Edificio</h1>
          <p>Control operativo de edificios, coberturas pendientes y estado de preplanilla.</p>
        </div>
        <div className="workflow-actions">
          <select value={selectedPeriod} onChange={(event) => {
            setSelectedPeriod(event.target.value);
            loadData(event.target.value);
          }}>
            {periods.map(period => (
              <option key={period.id} value={period.id}>{period.name}</option>
            ))}
          </select>
          <button className="workflow-btn secondary" onClick={() => loadData()}>
            <RefreshCw size={16} /> Recargar
          </button>
        </div>
      </header>

      <section className="workflow-grid">
        <div className="metric-panel"><span>Edificios</span><strong>{buildings.length}</strong></div>
        <div className="metric-panel"><span>Trabajadores activos</span><strong>{totals.workers}</strong></div>
        <div className="metric-panel"><span>Coberturas pendientes</span><strong>{totals.pending}</strong></div>
        <div className="metric-panel"><span>Preplanillas</span><strong>{totals.prepayrolls}</strong></div>
      </section>

      {loading ? (
        <div className="workflow-empty">Cargando operacion...</div>
      ) : buildings.length === 0 ? (
        <div className="workflow-empty">No hay edificios configurados.</div>
      ) : (
        <table className="workflow-table">
          <thead>
            <tr>
              <th>Edificio</th>
              <th>Centro de costo</th>
              <th>RUC empleador</th>
              <th>Personal</th>
              <th>Coberturas</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {buildings.map(building => (
              <tr key={building.id}>
                <td>{building.name}</td>
                <td>{building.cost_center || 'Sin centro'}</td>
                <td>{building.employer_ruc || 'Sin RUC'}</td>
                <td>{building.active_workers || 0}</td>
                <td>
                  {Number(building.pending_coverages || 0) > 0 ? (
                    <span className="workflow-status warn"><AlertTriangle size={14} /> {building.pending_coverages}</span>
                  ) : (
                    <span className="workflow-status ok">Sin pendientes</span>
                  )}
                </td>
                <td><span className="workflow-status">{building.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
