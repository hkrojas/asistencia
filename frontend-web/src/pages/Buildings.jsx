import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  Plus, 
  MapPin, 
  Search,
  X
} from 'lucide-react';
import { getBuildings, createBuilding, getPairingCode } from '../services/api';
import './Buildings.css';

const Buildings = () => {
  const [buildings, setBuildings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', address: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [pairingCode, setPairingCode] = useState(null);
  const [showPairingModal, setShowPairingModal] = useState(false);
  const [selectedBuilding, setSelectedBuilding] = useState(null);

  const fetchBuildings = async () => {
    setLoading(true);
    try {
      const response = await getBuildings();
      setBuildings(response.data);
    } catch (error) {
      console.error('Error fetching buildings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name) return;

    setIsSubmitting(true);
    try {
      await createBuilding(formData);
      setShowModal(false);
      setFormData({ name: '', address: '' });
      fetchBuildings();
    } catch (error) {
      console.error('Error creating building:', error);
      alert('Error al crear la sede');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGetPairingCode = async (building) => {
    setSelectedBuilding(building);
    try {
      const response = await getPairingCode(building.id);
      setPairingCode(response.data.code);
      setShowPairingModal(true);
    } catch (error) {
      console.error('Error generating pairing code:', error);
      alert('Error al generar código de emparejamiento');
    }
  };

  useEffect(() => {
    let cancelled = false;

    const loadInitialBuildings = async () => {
      try {
        const response = await getBuildings();
        if (!cancelled) {
          setBuildings(response.data);
        }
      } catch (error) {
        console.error('Error fetching buildings:', error);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadInitialBuildings();

    return () => {
      cancelled = true;
    };
  }, []);

  const filteredBuildings = buildings.filter(b => 
    b.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (b.address && b.address.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="buildings-container">
      <header className="view-header">
        <div className="header-left">
          <h1>Gestión de Sedes</h1>
          <p>Administra las locaciones y centros de trabajo</p>
        </div>
        <button className="add-btn" onClick={() => setShowModal(true)}>
          <Plus size={20} />
          <span>Nueva Sede</span>
        </button>
      </header>

      <div className="search-bar">
        <Search size={20} color="#6c757d" />
        <input 
          type="text" 
          placeholder="Buscar sede por nombre o dirección..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="content-card">
        {loading ? (
          <div className="loading-state">Cargando sedes...</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Sede</th>
                <th>Dirección</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredBuildings.length > 0 ? (
                filteredBuildings.map((building) => (
                  <tr key={building.id}>
                    <td>
                      <div className="building-info">
                        <Building2 size={18} color="#001a33" />
                        <span>{building.name}</span>
                      </div>
                    </td>
                    <td>
                      <div className="address-info">
                        <MapPin size={16} color="#6c757d" />
                        <span>{building.address || 'N/A'}</span>
                      </div>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button className="text-btn" style={{ marginRight: '12px' }}>Editar</button>
                        <button className="pair-btn" onClick={() => handleGetPairingCode(building)}>
                          Vincular Kiosco
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="3" style={{ textAlign: 'center', padding: '40px' }}>
                    No se encontraron sedes.
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
              <h2>Registrar Nueva Sede</h2>
              <button className="close-btn" onClick={() => setShowModal(false)}>
                <X size={24} />
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Nombre de la Sede</label>
                <input 
                  type="text" 
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="Ej: Oficina Central, Almacén Norte..."
                  required
                />
              </div>
              <div className="form-group">
                <label>Dirección</label>
                <input 
                  type="text" 
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                  placeholder="Calle, Número, Ciudad..."
                />
              </div>
              <div className="modal-footer">
                <button type="button" className="cancel-btn" onClick={() => setShowModal(false)}>
                  Cancelar
                </button>
                <button type="submit" className="submit-btn" disabled={isSubmitting}>
                  {isSubmitting ? 'Guardando...' : 'Crear Sede'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showPairingModal && (
        <div className="modal-overlay">
          <div className="modal-content pairing-modal">
            <div className="modal-header">
              <h2>Vincular Nuevo Kiosco</h2>
              <button className="close-btn" onClick={() => setShowPairingModal(false)}>
                <X size={24} />
              </button>
            </div>
            <div className="pairing-body" style={{ textAlign: 'center', padding: '20px 0' }}>
              <p>Ingrese este código en la aplicación móvil para la sede: <br/> <strong>{selectedBuilding?.name}</strong></p>
              <div className="pairing-code-display" style={{ 
                fontSize: '48px', 
                fontWeight: 'bold', 
                letterSpacing: '8px', 
                margin: '24px 0',
                color: '#0056b3',
                background: '#f8f9fa',
                padding: '20px',
                borderRadius: '12px',
                border: '2px dashed #dee2e6'
              }}>
                {pairingCode}
              </div>
              <p style={{ color: '#6c757d', fontSize: '14px' }}>Este código expira en 15 minutos.</p>
            </div>
            <div className="modal-footer">
              <button className="submit-btn" onClick={() => setShowPairingModal(false)}>
                Entendido
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Buildings;
