import React, { useState } from 'react';
import { createSalaryPaymentBatch, generatePayrollPayslips } from '../services/api';
import './WorkflowPages.css';

export default function Payments() {
  const [payrollRunId, setPayrollRunId] = useState('');
  const [message, setMessage] = useState('');
  const [batch, setBatch] = useState(null);

  const generate = async () => {
    setMessage('');
    try {
      await generatePayrollPayslips({ payroll_run_id: payrollRunId });
      setMessage('Boletas de pago de remuneraciones generadas para la planilla cerrada.');
    } catch (error) {
      setMessage(error.response?.data?.error || 'No se pudieron generar boletas de pago.');
    }
  };

  const prepare = async () => {
    setMessage('');
    try {
      const { data } = await createSalaryPaymentBatch({ payroll_run_id: payrollRunId });
      setBatch(data);
      setMessage('Lote de pago de sueldos preparado.');
    } catch (error) {
      setMessage(error.response?.data?.error || 'No se pudo preparar el pago de sueldos.');
    }
  };

  return (
    <div className="workflow-page">
      <header className="workflow-header">
        <div>
          <h1>Boletas de pago de remuneraciones</h1>
          <p>Pagos de sueldos y lotes de pago de sueldos desde una planilla cerrada.</p>
        </div>
      </header>

      <div className="metric-panel">
        <span>ID de planilla cerrada</span>
        <input
          value={payrollRunId}
          onChange={event => setPayrollRunId(event.target.value)}
          placeholder="UUID de payroll_run"
          style={{ marginTop: 10, width: '100%', padding: 10 }}
        />
      </div>

      <div className="workflow-actions" style={{ marginTop: 16 }}>
        <button className="workflow-btn secondary" onClick={generate} disabled={!payrollRunId}>Generar boletas de pago</button>
        <button className="workflow-btn" onClick={prepare} disabled={!payrollRunId}>Preparar pagos de sueldos</button>
      </div>

      {message && <p className="workflow-empty">{message}</p>}
      {batch && (
        <table className="workflow-table">
          <thead><tr><th>Lote</th><th>Estado</th></tr></thead>
          <tbody><tr><td>{batch.id}</td><td>{batch.state}</td></tr></tbody>
        </table>
      )}
    </div>
  );
}
