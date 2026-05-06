import { useState, useEffect } from 'react';

export function InventarioArea({ allowed, username, onRefresh }) {
  const [activeTab, setActiveTab] = useState('items');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState(''); // entrada, salida, ajuste

  const apiUrl = import.meta.env.VITE_OPERACIONES_API_URL ?? 'http://localhost:8001';

  useEffect(() => {
    if (allowed) {
      loadItems();
    }
  }, [allowed, activeTab]);

  async function loadItems() {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${apiUrl}/items`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Name': username || 'guest',
        },
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const data = await response.json();
      setItems(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando items');
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  async function updateStock(itemId, quantityChange, reason, reference) {
    try {
      const response = await fetch(`${apiUrl}/items/${itemId}/stock/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Name': username || 'guest',
        },
        body: JSON.stringify({
          quantity_change: quantityChange,
          reason,
          reference_id: reference,
        }),
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      setShowModal(false);
      setSelectedItem(null);
      loadItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error actualizando stock');
    }
  }

  if (!allowed) {
    return (
      <div className="locked-area">
        <div className="lock-icon">🔒</div>
        <h2>Acceso Restringido</h2>
        <p>Inventario está grisado porque tu rol no tiene acceso.</p>
        <p className="lock-description">
          Control de stock, entradas, salidas y movimientos operativos.
        </p>
      </div>
    );
  }

  return (
    <div className="module-area">
      <div className="area-header">
        <h2>📦 Inventario</h2>
        <p>Control de stock, entradas, salidas y movimientos operativos.</p>
      </div>

      <div className="sub-tabs">
        <button
          className={`sub-tab ${activeTab === 'items' ? 'active' : ''}`}
          onClick={() => setActiveTab('items')}
        >
          Items
        </button>
        <button
          className={`sub-tab ${activeTab === 'movimientos' ? 'active' : ''}`}
          onClick={() => setActiveTab('movimientos')}
        >
          Movimientos
        </button>
        <button
          className={`sub-tab ${activeTab === 'alertas' ? 'active' : ''}`}
          onClick={() => setActiveTab('alertas')}
        >
          Alertas
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {activeTab === 'items' && (
        <div className="tab-content">
          <div className="section-header">
            <h3>Tabla de Items</h3>
            <button className="btn btn-primary" onClick={loadItems} disabled={loading}>
              {loading ? '⟳ Cargando...' : '↻ Refrescar'}
            </button>
          </div>

          {loading ? (
            <p className="text-center">Cargando items...</p>
          ) : items.length === 0 ? (
            <p className="text-center">No hay items disponibles</p>
          ) : (
            <div className="table-wrapper">
              <table className="items-table">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>Nombre</th>
                    <th>Cantidad</th>
                    <th>Mínimo</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id} className={item.below_minimum ? 'row-alert' : ''}>
                      <td className="sku">{item.sku}</td>
                      <td>{item.name}</td>
                      <td className="qty">{item.quantity_on_hand}</td>
                      <td className="threshold">{item.minimum_threshold}</td>
                      <td>
                        {item.below_minimum ? (
                          <span className="badge badge-warning">⚠ Bajo Stock</span>
                        ) : (
                          <span className="badge badge-success">✓ Normal</span>
                        )}
                      </td>
                      <td className="actions">
                        <button
                          className="btn-sm btn-info"
                          onClick={() => {
                            setSelectedItem(item);
                            setModalType('entrada');
                            setShowModal(true);
                          }}
                          title="Entrada de mercancía"
                        >
                          📥
                        </button>
                        <button
                          className="btn-sm btn-warning"
                          onClick={() => {
                            setSelectedItem(item);
                            setModalType('salida');
                            setShowModal(true);
                          }}
                          title="Salida de mercancía"
                        >
                          📤
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'movimientos' && (
        <div className="tab-content">
          <h3>Movimientos Registrados</h3>
          <p className="text-muted">Historial de entradas, salidas y ajustes de stock.</p>
          <div className="coming-soon">📋 Historial de movimientos - Próximamente</div>
        </div>
      )}

      {activeTab === 'alertas' && (
        <div className="tab-content">
          <h3>Alertas de Stock</h3>
          <p className="text-muted">Items que requieren atención inmediata.</p>
          {items.filter((i) => i.below_minimum).length === 0 ? (
            <div className="success-message">✓ Todos los items están en stock normal</div>
          ) : (
            <div className="alerts-list">
              {items
                .filter((i) => i.below_minimum)
                .map((item) => (
                  <div key={item.id} className="alert-card">
                    <div className="alert-icon">⚠</div>
                    <div className="alert-content">
                      <h4>{item.name}</h4>
                      <p>
                        Stock actual: <strong>{item.quantity_on_hand}</strong> | Mínimo: <strong>{item.minimum_threshold}</strong>
                      </p>
                      <p className="text-muted">SKU: {item.sku}</p>
                    </div>
                    <button
                      className="btn btn-primary"
                      onClick={() => {
                        setSelectedItem(item);
                        setModalType('entrada');
                        setShowModal(true);
                      }}
                    >
                      Repostar
                    </button>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}

      {/* Modal para entrada/salida */}
      {showModal && selectedItem && (
        <StockMovementModal
          item={selectedItem}
          type={modalType}
          onClose={() => {
            setShowModal(false);
            setSelectedItem(null);
          }}
          onSubmit={(quantity, reason, reference) => {
            const change = modalType === 'entrada' ? quantity : -quantity;
            updateStock(selectedItem.id, change, reason, reference);
          }}
        />
      )}
    </div>
  );
}

function StockMovementModal({ item, type, onClose, onSubmit }) {
  const [quantity, setQuantity] = useState('');
  const [reason, setReason] = useState('');
  const [reference, setReference] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const isEntrada = type === 'entrada';
  const title = isEntrada ? '📥 Entrada de Mercancía' : '📤 Salida de Mercancía';
  const reasons = isEntrada
    ? ['Compra recibida', 'Devolución de cliente', 'Ajuste', 'Otro']
    : ['Venta', 'Devolución a proveedor', 'Daño/Pérdida', 'Otro'];

  async function handleSubmit(e) {
    e.preventDefault();
    if (!quantity || !reason) return;

    setSubmitting(true);
    try {
      await onSubmit(parseInt(quantity), reason, reference);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label>Item</label>
            <input type="text" value={item.name} disabled className="form-input" />
            <small>{item.sku}</small>
          </div>

          <div className="form-group">
            <label>Stock Actual</label>
            <input type="number" value={item.quantity_on_hand} disabled className="form-input" />
          </div>

          <div className="form-group">
            <label>Cantidad</label>
            <input
              type="number"
              min="1"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="Ingresa cantidad"
              className="form-input"
              required
            />
          </div>

          <div className="form-group">
            <label>Razón</label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="form-input"
              required
            >
              <option value="">Selecciona una razón</option>
              {reasons.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Referencia (opcional)</label>
            <input
              type="text"
              value={reference}
              onChange={(e) => setReference(e.target.value)}
              placeholder="PO, RMA, etc."
              className="form-input"
            />
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Guardando...' : 'Guardar Movimiento'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
