import React, { useEffect, useState } from 'react';
import {
  closePayrollRun,
  createPayrollRun,
  getPayrollConsolidation,
  getPayrollPeriods,
  validatePayrollFinance,
  validatePayrollHr,
} from '../services/api';
import './WorkflowPages.css';

export default function Payroll() {
  const [periods, setPeriods] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('');
  const [consolidation, setConsolidation] = useState(null);
  const [payrollRun, setPayrollRun] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    getPayrollPeriods().then(({ data }) => {
      setPeriods(data);
      const active = data.find(period => period.state === 'open') || data[0];
      setSelectedPeriod(active?.id || '');
    });
  }, []);

  useEffect(() => {
    if (!selectedPeriod) return;
    getPayrollConsolidation(selectedPeriod)
      .then(({ data }) => setConsolidation(data))
      .catch(() => setConsolidation(null));
  }, [selectedPeriod]);

  const createRun = async () => {
    setMessage('');
    try {
      const { data } = await createPayrollRun({ payroll_period_id: selectedPeriod });
      setPayrollRun(data);
      setMessage('Planilla central creada.');
    } catch (error) {
      setMessage(error.response?.data?.error || 'No se pudo crear la planilla.');
    }
  };

  const validateHr = async () => {
    if (!payrollRun?.id) return;
    await validatePayrollHr(payrollRun.id);
    setPayrollRun(prev => ({ ...prev, state: 'hr_validated' }));
  };

  const validateFinance = async () => {
    if (!payrollRun?.id) return;
    await validatePayrollFinance(payrollRun.id);
    setPayrollRun(prev => ({ ...prev, state: 'finance_validated' }));
  };

  const closeRun = async () => {
    if (!payrollRun?.id) return;
    await closePayrollRun(payrollRun.id, { reason: 'Cierre desde panel de planilla' });
    setPayrollRun(prev => ({ ...prev, state: 'closed' }));
    setMessage('Planilla cerrada con snapshot.');
  };

  const states = consolidation?.prepayroll_states || {};

  return (
    <div className="workflow-page">
      <header className="workflow-header">
        <div>
          <h1>Planilla Central</h1>
          <p>Consolidacion RRHH, validaciones, cierre versionado y snapshot de planilla.</p>
        </div>
        <select value={selectedPeriod} onChange={event => setSelectedPeriod(event.target.value)}>
          {periods.map(period => <option key={period.id} value={period.id}>{period.name}</option>)}
        </select>
      </header>

      <section className="workflow-grid">
        <div className="metric-panel"><span>Preplanillas aprobadas</span><strong>{states.approved_by_hr || 0}</strong></div>
        <div className="metric-panel"><span>Observadas</span><strong>{states.observed_by_hr || 0}</strong></div>
        <div className="metric-panel"><span>Movimientos</span><strong>{consolidation?.workers_with_movements || 0}</strong></div>
        <div className="metric-panel"><span>Estado planilla</span><strong>{payrollRun?.state || 'Sin crear'}</strong></div>
      </section>

      <div className="workflow-actions">
        <button className="workflow-btn" onClick={createRun} disabled={!selectedPeriod}>Crear planilla</button>
        <button className="workflow-btn secondary" onClick={validateHr} disabled={!payrollRun?.id}>Validar RRHH</button>
        <button className="workflow-btn secondary" onClick={validateFinance} disabled={!payrollRun?.id}>Validar Finanzas</button>
        <button className="workflow-btn" onClick={closeRun} disabled={payrollRun?.state !== 'finance_validated'}>Cerrar planilla</button>
      </div>

      {message && <p className="workflow-empty">{message}</p>}
    </div>
  );
}

