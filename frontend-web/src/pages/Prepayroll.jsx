import React, { useEffect, useMemo, useState } from 'react';
import {
  approveBuildingPrepayroll,
  generateBuildingPrepayroll,
  getBuildings,
  getPayrollConsolidation,
  getPayrollPeriods,
  sendBuildingPrepayroll,
} from '../services/api';
import './WorkflowPages.css';

export default function Prepayroll() {
  const [periods, setPeriods] = useState([]);
  const [buildings, setBuildings] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('');
  const [selectedBuilding, setSelectedBuilding] = useState('');
  const [consolidation, setConsolidation] = useState(null);
  const [lastPrepayroll, setLastPrepayroll] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    async function load() {
      const [periodsRes, buildingsRes] = await Promise.all([getPayrollPeriods(), getBuildings()]);
      setPeriods(periodsRes.data);
      setBuildings(buildingsRes.data);
      const active = periodsRes.data.find(p => p.state === 'open') || periodsRes.data[0];
      setSelectedPeriod(active?.id || '');
      setSelectedBuilding(buildingsRes.data[0]?.id || '');
    }
    load();
  }, []);

  useEffect(() => {
    if (!selectedPeriod) return;
    getPayrollConsolidation(selectedPeriod)
      .then(res => setConsolidation(res.data))
      .catch(() => setConsolidation(null));
  }, [selectedPeriod]);

  const states = useMemo(() => consolidation?.prepayroll_states || {}, [consolidation]);

  const generate = async () => {
    setMessage('');
    const { data } = await generateBuildingPrepayroll({
      building_id: selectedBuilding,
      payroll_period_id: selectedPeriod,
    });
    setLastPrepayroll(data);
    setMessage('Preplanilla generada.');
  };

  const send = async () => {
    if (!lastPrepayroll?.id) return;
    setMessage('');
    try {
      await sendBuildingPrepayroll(lastPrepayroll.id);
      setMessage('Preplanilla enviada a RRHH.');
    } catch (error) {
      const blockers = error.response?.data?.blockers;
      setMessage(blockers ? `Bloqueada: ${blockers.errors.join(', ')}` : 'No se pudo enviar.');
    }
  };

  const approve = async () => {
    if (!lastPrepayroll?.id) return;
    await approveBuildingPrepayroll(lastPrepayroll.id);
    setMessage('Preplanilla aprobada por RRHH.');
  };

  return (
    <div className="workflow-page">
      <header className="workflow-header">
        <div>
          <h1>Preplanilla por Edificio</h1>
          <p>Generacion, envio, observacion y aprobacion de preplanillas por edificio.</p>
        </div>
        <div className="workflow-actions">
          <select value={selectedPeriod} onChange={event => setSelectedPeriod(event.target.value)}>
            {periods.map(period => <option key={period.id} value={period.id}>{period.name}</option>)}
          </select>
          <select value={selectedBuilding} onChange={event => setSelectedBuilding(event.target.value)}>
            {buildings.map(building => <option key={building.id} value={building.id}>{building.name}</option>)}
          </select>
        </div>
      </header>

      <section className="workflow-grid">
        <div className="metric-panel"><span>Borrador</span><strong>{states.draft || 0}</strong></div>
        <div className="metric-panel"><span>Enviadas</span><strong>{states.sent_to_hr || 0}</strong></div>
        <div className="metric-panel"><span>Observadas</span><strong>{states.observed_by_hr || 0}</strong></div>
        <div className="metric-panel"><span>Aprobadas</span><strong>{states.approved_by_hr || 0}</strong></div>
      </section>

      <div className="workflow-actions">
        <button className="workflow-btn" onClick={generate} disabled={!selectedPeriod || !selectedBuilding}>
          Generar preplanilla
        </button>
        <button className="workflow-btn secondary" onClick={send} disabled={!lastPrepayroll?.id}>
          Enviar a RRHH
        </button>
        <button className="workflow-btn secondary" onClick={approve} disabled={!lastPrepayroll?.id}>
          Aprobar RRHH
        </button>
      </div>

      {message && <p className="workflow-empty">{message}</p>}
      {lastPrepayroll?.blockers && (
        <table className="workflow-table">
          <thead>
            <tr><th>Validacion</th><th>Resultado</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>Bloqueos criticos</td>
              <td>{lastPrepayroll.blockers.blocker_count}</td>
            </tr>
            <tr>
              <td>Detalle</td>
              <td>{lastPrepayroll.blockers.errors?.join(', ') || 'Sin errores'}</td>
            </tr>
          </tbody>
        </table>
      )}
    </div>
  );
}

