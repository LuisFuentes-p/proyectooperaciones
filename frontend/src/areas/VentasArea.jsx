import { useState, useEffect } from 'react';

export function VentasArea({ allowed, username, onRefresh }) {
  const [activeTab, setActiveTab] = useState('ordenes');
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [customers, setCustomers] = useState([]);
  const [items, setItems] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newOrder, setNewOrder] = useState({
    item_id: '',
    customer_id: '',
    quantity: '',
  });

  const apiUrl = import.meta.env.VITE_OPERACIONES_API_URL ?? 'http://localhost:8001';

  useEffect(() => {
    if (allowed) {
      loadSalesOrders();
      loadItems();
    }
  }, [allowed, activeTab]);

  async function loadSalesOrders(status = null) {
    setLoading(true);
    setError('');
    try {
      const url = status ? `${apiUrl}/sales-orders?status=${status}` : `${apiUrl}/sales-orders`;
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

  async function loadItems() {
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
      console.error('Error loading items:', err);
    }
  }

  async function createSalesOrder(e) {
    e.preventDefault();
    if (!newOrder.item_id || !newOrder.customer_id || !newOrder.quantity) return;

    try {
      const response = await fetch(`${apiUrl}/sales-orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Name': username || 'guest',
        },
        body: JSON.stringify({
          item_id: parseInt(newOrder.item_id),
          customer_id: parseInt(newOrder.customer_id),
          quantity: parseInt(newOrder.quantity),
        }),
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      setShowCreateForm(false);
      setNewOrder({ item_id: '', customer_id: '', quantity: '' });
      loadSalesOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error creando orden');
    }
  }

  async function updateOrderStatus(orderId, newStatus) {
    try {
      const response = await fetch(`${apiUrl}/sales-orders/${orderId}/status`, {
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
      loadSalesOrders();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error actualizando estado');
    }
  }

  async function downloadInvoice(orderId) {
    try {
      const response = await fetch(`${apiUrl}/sales-orders/${orderId}/invoice`, {
        method: 'GET',
        headers: {
          'X-User-Name': username || 'guest',
        },
      });

      if (!response.ok) {
        throw new Error('Invoice no disponible');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice-${orderId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error descargando factura');
    }
  }

  if (!allowed) {
    return (
      <div className="locked-area">
        <div className="lock-icon">🔒</div>
        <h2>Acceso Restringido</h2>
        <p>Ventas está grisado porque tu rol no tiene acceso.</p>
        <p className="lock-description">Portal de ventas y facturación de clientes.</p>
      </div>
    );
  }

  const statusColors = {
    pending: 'badge-warning',
    confirmed: 'badge-info',
    shipped: 'badge-primary',
    delivered: 'badge-success',
    cancelled: 'badge-danger',
  };

  return (
    <div className="module-area">
      <div className="area-header">
        <h2>💰 Ventas</h2>
        <p>Portal de ventas y facturación de clientes.</p>
      </div>

      <div className="sub-tabs">
        <button
          className={`sub-tab ${activeTab === 'ordenes' ? 'active' : ''}`}
          onClick={() => setActiveTab('ordenes')}
        >
          Órdenes
        </button>
        <button
          className={`sub-tab ${activeTab === 'clientes' ? 'active' : ''}`}
          onClick={() => setActiveTab('clientes')}
        >
          Clientes
        </button>
        <button
          className={`sub-tab ${activeTab === 'estadisticas' ? 'active' : ''}`}
          onClick={() => setActiveTab('estadisticas')}
        >
          Estadísticas
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {activeTab === 'ordenes' && (
        <div className="tab-content">
          <div className="section-header">
            <h3>Órdenes de Venta</h3>
            <button className="btn btn-primary" onClick={() => setShowCreateForm(true)}>
              + Nueva Orden
            </button>
          </div>

          {loading ? (
            <p className="text-center">Cargando órdenes...</p>
          ) : orders.length === 0 ? (
            <p className="text-center">No hay órdenes de venta registradas</p>
          ) : (
            <div className="table-wrapper">
              <table className="orders-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Cliente</th>
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
                      <td className="order-id">SO-{order.id}</td>
                      <td>{order.customer_name}</td>
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
                          onClick={() => downloadInvoice(order.id)}
                          title="Descargar factura"
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

          {showCreateForm && (
            <CreateOrderModal
              items={items}
              onClose={() => setShowCreateForm(false)}
              onSubmit={createSalesOrder}
              newOrder={newOrder}
              setNewOrder={setNewOrder}
            />
          )}
        </div>
      )}

      {activeTab === 'clientes' && (
        <div className="tab-content">
          <h3>Clientes</h3>
          <p className="text-muted">Gestión de clientes y contactos.</p>
          <div className="coming-soon">👥 Directorio de clientes - Próximamente</div>
        </div>
      )}

      {activeTab === 'estadisticas' && (
        <div className="tab-content">
          <h3>Estadísticas de Ventas</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <h4>Órdenes Totales</h4>
              <div className="stat-value">{orders.length}</div>
            </div>
            <div className="stat-card">
              <h4>Pendientes</h4>
              <div className="stat-value">{orders.filter((o) => o.status === 'pending').length}</div>
            </div>
            <div className="stat-card">
              <h4>Entregadas</h4>
              <div className="stat-value">{orders.filter((o) => o.status === 'delivered').length}</div>
            </div>
            <div className="stat-card">
              <h4>Total Vendido</h4>
              <div className="stat-detail">
                ${orders.reduce((sum, o) => sum + (o.total_amount || 0), 0).toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de detalle */}
      {showDetail && selectedOrder && (
        <SalesOrderDetailModal
          order={selectedOrder}
          statusColors={statusColors}
          onClose={() => {
            setShowDetail(false);
            setSelectedOrder(null);
          }}
          onStatusChange={(newStatus) => updateOrderStatus(selectedOrder.id, newStatus)}
          onDownloadInvoice={() => downloadInvoice(selectedOrder.id)}
        />
      )}
    </div>
  );
}

function CreateOrderModal({ items, onClose, onSubmit, newOrder, setNewOrder }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Nueva Orden de Venta</h3>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <form onSubmit={onSubmit} className="modal-form">
          <div className="form-group">
            <label>Item</label>
            <select
              value={newOrder.item_id}
              onChange={(e) => setNewOrder({ ...newOrder, item_id: e.target.value })}
              className="form-input"
              required
            >
              <option value="">Selecciona un item</option>
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.sku} - {item.name} (${item.unit_price.toFixed(2)}) - Stock: {item.quantity_on_hand}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Cantidad</label>
            <input
              type="number"
              min="1"
              value={newOrder.quantity}
              onChange={(e) => setNewOrder({ ...newOrder, quantity: e.target.value })}
              placeholder="Ingresa cantidad"
              className="form-input"
              required
            />
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary">
              Crear Orden
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SalesOrderDetailModal({ order, statusColors, onClose, onStatusChange, onDownloadInvoice }) {
  const nextStatuses = {
    pending: ['confirmed', 'cancelled'],
    confirmed: ['shipped', 'cancelled'],
    shipped: ['delivered', 'cancelled'],
    delivered: [],
    cancelled: [],
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-lg" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Orden de Venta #{order.id}</h3>
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
              <label>Cliente:</label>
              <span>{order.customer_name}</span>
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
          <button className="btn btn-primary" onClick={onDownloadInvoice}>
            📄 Descargar Factura
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
