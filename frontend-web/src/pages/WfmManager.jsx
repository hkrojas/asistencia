import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Clock, 
  CheckCircle2, 
  ChevronRight, 
  RefreshCw,
  Search
} from 'lucide-react';
import { getWfmIssues, resolveWfmIssue } from '../services/api';
import ResolveModal from './ResolveModal';
import './WfmManager.css';

const normalizeAnomalyFlags = (flags) => {
  if (Array.isArray(flags)) {
    return flags;
  }

  if (!flags) {
    return [];
  }

  if (typeof flags !== 'string') {
    return [String(flags)];
  }

  try {
    const parsed = JSON.parse(flags);
    if (Array.isArray(parsed)) {
      return parsed;
    }
    return parsed ? [String(parsed)] : [];
  } catch {
    return [flags];
  }
};

const WfmManager = () => {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchIssues = async () => {
    setLoading(true);
    try {
      const response = await getWfmIssues();
      setIssues(response.data);
    } catch (error) {
      console.error('Error fetching WFM issues:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;

    const loadInitialIssues = async () => {
      try {
        const response = await getWfmIssues();
        if (!cancelled) {
          setIssues(response.data);
        }
      } catch (error) {
        console.error('Error fetching WFM issues:', error);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadInitialIssues();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleResolve = async (id, data) => {
    try {
      await resolveWfmIssue(id, data);
      setSelectedIssue(null);
      fetchIssues(); // Recargar lista
    } catch (error) {
      alert('Error al resolver la anomalía: ' + (error.response?.data?.error || error.message));
    }
  };

  const filteredIssues = issues.filter(issue => 
    issue.full_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="wfm-container">
      <header className="wfm-header">
        <div className="header-title">
          <h1>Monitor WFM</h1>
          <p>Gestión de excepciones y anomalías de asistencia</p>
        </div>
        <div className="header-actions">
          <button className="refresh-btn" onClick={fetchIssues} disabled={loading}>
            <RefreshCw size={18} className={loading ? 'spin' : ''} />
            Actualizar
          </button>
        </div>
      </header>

      <div className="wfm-filters">
        <div className="search-box">
          <Search size={20} />
          <input 
            type="text" 
            placeholder="Buscar por empleado..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="filter-tags">
          <span className="tag-label">Pendientes: {issues.length}</span>
        </div>
      </div>

      <div className="wfm-content">
        {loading && <div className="loading-state">Cargando excepciones...</div>}
        
        {!loading && filteredIssues.length === 0 && (
          <div className="empty-state">
            <CheckCircle2 size={48} color="#10b981" />
            <h3>¡Todo al día!</h3>
            <p>No hay anomalías pendientes de resolución en el periodo actual.</p>
          </div>
        )}

        {!loading && filteredIssues.length > 0 && (
          <div className="issues-table-container">
            <table className="wfm-table">
              <thead>
                <tr>
                  <th>Empleado</th>
                  <th>Fecha</th>
                  <th>Estado / Problema</th>
                  <th>Marcaciones</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {filteredIssues.map(issue => {
                  const anomalyFlags = normalizeAnomalyFlags(issue.anomaly_flags);
                  const isOrphan = anomalyFlags.includes('orphan_in') || anomalyFlags.includes('orphan_out');
                  
                  return (
                    <tr key={issue.id} className={isOrphan ? 'row-critical' : 'row-warning'}>
                      <td>
                        <div className="employee-info">
                          <span className="emp-name">{issue.full_name}</span>
                        </div>
                      </td>
                      <td>{issue.logical_date}</td>
                      <td>
                        <div className={`status-badge ${isOrphan ? 'bad' : 'warn'}`}>
                          {isOrphan ? <AlertTriangle size={14} /> : <Clock size={14} />}
                          <span>
                            {isOrphan ? "Marcación Incompleta" : "Extra por Aprobar"}
                          </span>
                        </div>
                        {anomalyFlags.length > 0 && (
                          <div className="anomaly-tags">
                            {anomalyFlags.map(flag => (
                              <span key={flag} className="flag-tag">{flag}</span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td>
                        <div className="punch-summary">
                          <span>IN: {issue.first_punch_in ? new Date(issue.first_punch_in).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '--:--'}</span>
                          <span>OUT: {issue.last_punch_out ? new Date(issue.last_punch_out).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '--:--'}</span>
                        </div>
                      </td>
                      <td>
                        <button 
                          className="resolve-btn"
                          onClick={() => setSelectedIssue(issue)}
                        >
                          Resolver
                          <ChevronRight size={16} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedIssue && (
        <ResolveModal 
          key={selectedIssue.id}
          issue={selectedIssue} 
          onClose={() => setSelectedIssue(null)}
          onResolve={handleResolve}
        />
      )}
    </div>
  );
};

export default WfmManager;
