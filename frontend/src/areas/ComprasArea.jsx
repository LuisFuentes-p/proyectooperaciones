import { useState, useEffect } from 'react';

export function ComprasArea({ allowed, username, onRefresh }) {
  const [activeTab, setActiveTab] = useState('ordenes');
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stats, setStats] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  const apiUrl = import.meta.env.VITE_OPERACIONES_API_URL ?? 'http://localhost:8001';

  useEffect(() => {
    if (allowed) {
      loadOrders();
      loadStats();
    }
  }, [allowed, activeTab]);

  async function loadOrders(status = null) {
    setLoading(true);
    setError('');
    try {
      const url = status ? `${apiUrl}/purchase-orders?status=${status}` : `${apiUrl}/purchase-orders`;
      const response = await fetch(url, {
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
      setOrders(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando órdenes');
      setOrders([]);
    } finally {
      setLoading(false);
    }
  }

  async function loadStats() {
    try {
      const response = await fetch(`${apiUrl}/stats/order-summary`, {
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
      setStats(data);
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  }

  async function updateOrderStatus(orderId, newStatus) {
    try {
      const response = await fetch(`${apiUrl}/purchase-orders/${orderId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Name': username || 'guest',
        },
        body: JSON.stringify({ new_status: newStatus }),
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      setShowDetail(false);
      setSelectedOrder(null);
      loadOrders();
      loadStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error actualizando estado');
    }
  }

  async function downloadPdf(orderId) {
    try {
      const response = await fetch(`${apiUrl}/purchase-orders/${orderId}/pdf`, {
        method: 'GET',
        headers: {
          'X-User-Name': username || 'guest',
        },
      });

      if (!response.ok) {
        throw new Error('PDF no disponible');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `purchase-order-${orderId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error descargando PDF');
    }
  }

  if (!allowed) {
    return (
      <div className="locked-area">
        <div className="lock-icon">🔒</div>
        <h2>Acceso Restringido</h2>
        <p>Compras está grisado porque tu rol no tiene acceso.</p>
        <p className="lock-description">Portal del POS y abastecimiento de compras.</p>
      </div>
    );
  }

  const statusColors = {
    pending: 'badge-warning',
    confirmed: 'badge-info',
    shipped: 'badge-primary',
    received: 'badge-success',
    cancelled: 'badge-danger',
  };

  return (
    <div className="module-area">
      <div className="area-header">
        <h2>🛒 Compras</h2>
        <p>Portal del POS y abastecimiento de compras.</p>
      </div>

      <div className="sub-tabs">
        <button
          className={`sub-tab ${activeTab === 'ordenes' ? 'active' : ''}`}
          onClick={() => setActiveTab('ordenes')}
        >
          Órdenes
        </button>
        <button
          className={`sub-tab ${activeTab === 'estadisticas' ? 'active' : ''}`}
          onClick={() => setActiveTab('estadisticas')}
        >
          Estadísticas
        </button>
        <button
          className={`sub-tab ${activeTab === 'proveedores' ? 'active' : ''}`}
          onClick={() => setActiveTab('proveedores')}
        >
          Proveedores
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {activeTab === 'ordenes' && (
        <div className="tab-content">
          <div className="section-header">
            <h3>Órdenes de Compra</h3>
            <button className="btn btn-primary" onClick={() => loadOrders()} disabled={loading}>
              {loading ? '⟳ Cargando...' : '↻ Refrescar'}
            </button>
          </div>

          {loading ? (
            <p className="text-center">Cargando órdenes...</p>
          ) : orders.length === 0 ? (
            <p className="text-center">No hay órdenes disponibles</p>
          ) : (
            <div className="table-wrapper">
              <table className="orders-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Proveedor</th>
                    <th>Item</th>
                    <th>Cantidad</th>
                    <th>Total</th>
                    <th>Estado</th>
                    <th>Entrega</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={order.id}>
                      <td className="order-id">PO-{order.id}</td>
                      <td>{order.supplier_name}</td>
                      <td className="item-sku">{order.item_sku}</td>
                      <td className="qty">{order.quantity}</td>
                      <td className="amount">${order.total_amount?.toFixed(2)}</td>
                      <td>
                        <span className={`badge ${statusColors[order.status] || 'badge-secondary'}`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="date">
                        {order.expected_delivery_date
                          ? new Date(order.expected_delivery_date).toLocaleDateString()
                          : '-'}
                      </td>
                      <td className="actions">
                        <button
                          className="btn-sm btn-info"
                          onClick={() => {
                            setSelectedOrder(order);
                            setShowDetail(true);
                          }}
                          title="Ver detalles"
                        >
                          👁
                        </button>
                        <button
                          className="btn-sm btn-success"
                          onClick={() => downloadPdf(order.id)}
                          title="Descargar PDF"
                        >
                          📄
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

      {activeTab === 'estadisticas' && (
        <div className="tab-content">
          <h3>Resumen de Órdenes</h3>
          {stats ? (
            <div className="stats-grid">
              {Object.entries(stats).map(([status, data]) => (
                <div key={status} className="stat-card">
                  <h4 className="stat-label">{status}</h4>
                  <div className="stat-value">{data.count}</div>
                  <div className="stat-detail">${data.total_value?.toFixed(2)}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted">Cargando estadísticas...</p>
          )}
        </div>
      )}

      {activeTab === 'proveedores' && (
        <div className="tab-content">
          <h3>Proveedores</h3>
          <p className="text-muted">Gestión de proveedores y contactos.</p>
          <div className="coming-soon">📞 Directorio de proveedores - Próximamente</div>
        </div>
      )}

      {/* Modal de detalle */}
      {showDetail && selectedOrder && (
        <OrderDetailModal
          order={selectedOrder}
          statusColors={statusColors}
          onClose={() => {
            setShowDetail(false);
            setSelectedOrder(null);
          }}
          onStatusChange={(newStatus) => updateOrderStatus(selectedOrder.id, newStatus)}
          onDownloadPdf={() => downloadPdf(selectedOrder.id)}
        />
      )}
    </div>
  );
}

function OrderDetailModal({ order, statusColors, onClose, onStatusChange, onDownloadPdf }) {
  const nextStatuses = {
    pending: ['confirmed', 'cancelled'],
    confirmed: ['shipped', 'cancelled'],
    shipped: ['received', 'cancelled'],
    received: [],
    cancelled: [],
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-lg" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Orden de Compra #{order.id}</h3>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          <div className="detail-grid">
            <div className="detail-row">
              <label>Estado Actual:</label>
              <span className={`badge ${statusColors[order.status] || 'badge-secondary'}`}>
                {order.status}
              </span>
            </div>
            <div className="detail-row">
              <label>Proveedor:</label>
              <span>{order.supplier_name}</span>
            </div>
            <div className="detail-row">
              <label>Email:</label>
              <span>{order.supplier_email || '-'}</span>
            </div>
            <div className="detail-row">
              <label>Item:</label>
              <span>
                {order.item_sku} - {order.item_name}
              </span>
            </div>
            <div className="detail-row">
              <label>Cantidad:</label>
              <span>{order.quantity}</span>
            </div>
            <div className="detail-row">
              <label>Precio Unitario:</label>
              <span>${order.unit_price?.toFixed(2)}</span>
            </div>
            <div className="detail-row">
              <label>Total:</label>
              <span className="font-bold">${order.total_amount?.toFixed(2)}</span>
            </div>
            <div className="detail-row">
              <label>Fecha Creación:</label>
              <span>{new Date(order.created_at).toLocaleString()}</span>
            </div>
            <div className="detail-row">
              <label>Entrega Esperada:</label>
              <span>
                {order.expected_delivery_date
                  ? new Date(order.expected_delivery_date).toLocaleDateString()
                  : '-'}
              </span>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cerrar
          </button>
          <button className="btn btn-primary" onClick={onDownloadPdf}>
            📄 Descargar PDF
          </button>
          {nextStatuses[order.status]?.length > 0 && (
            <select
              defaultValue=""
              onChange={(e) => {
                if (e.target.value) onStatusChange(e.target.value);
              }}
              className="form-input"
              style={{ maxWidth: '150px' }}
            >
              <option value="">Cambiar Estado</option>
              {nextStatuses[order.status].map((status) => (
                <option key={status} value={status}>
                  → {status}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>
    </div>
  );
}
