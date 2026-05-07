Guía de Interacción — Microservicio Logística
Descripción General
El microservicio de logística es responsable de:
Monitorear niveles de inventario
Detectar productos bajo mínimo
Generar alertas automáticas
Coordinar solicitudes logísticas
Monitorear órdenes de compra
Gestionar entregas
Coordinar reposiciones con inventario y compras

Base URL
http://localhost:8003


Autenticación
Todos los endpoints requieren:
X-User-Name: nombre_usuario

Ejemplo:
X-User-Name: admin


Integración con Otros Microservicios
Microservicio
Relación
Inventario
Consulta stock, solicitudes y órdenes
Compras
Monitorea purchase orders
Finanzas
Consulta costos e impacto financiero
Frontend
Dashboard logístico y monitoreo


Flujo General
Inventario detecta stock bajo
        ↓
Logística genera alerta
        ↓
Se crea solicitud logística
        ↓
Compras procesa orden
        ↓
Inventario actualiza stock
        ↓
Logística marca solicitud como completada


ENDPOINTS

1. Health Check
GET /health
Verifica estado del servicio.
Response
{
  "status": "ok",
  "service": "logistica"
}


MONITOREO DE INVENTARIO

2. Obtener Productos Bajo Mínimo
GET /monitor/items-below-minimum
Retorna productos con stock inferior al mínimo permitido.
Headers
X-User-Name: admin

Response
[
  {
    "id": 1,
    "sku": "SKU-001",
    "name": "Laptop Dell XPS 13",
    "current_quantity": 2,
    "minimum_threshold": 5,
    "reorder_quantity": 10,
    "supplier_name": "TechSupply Inc",
    "unit_cost": 1200.0,
    "shortage": 3,
    "needs_reorder": true
  }
]


3. Obtener Productos Sin Stock
GET /monitor/stockout-items
Retorna productos completamente agotados.
Response
[
  {
    "id": 2,
    "sku": "SKU-002",
    "name": "Monitor LG",
    "reorder_quantity": 15,
    "supplier_name": "TechSupply Inc",
    "minimum_threshold": 5,
    "status": "STOCKOUT",
    "urgency": "CRITICAL"
  }
]


4. Dashboard General de Inventario
GET /monitor/stock-status-dashboard
Obtiene resumen global del inventario.
Response
{
  "total_items": 50,
  "stockout_count": 2,
  "below_minimum_count": 8,
  "critical_items": 2,
  "total_inventory_value": 25300.50,
  "timestamp": "2026-05-06T12:00:00"
}


ALERTAS AUTOMÁTICAS

5. Ejecutar Revisión de Alertas
POST /monitor/check-and-alert
Genera alertas automáticamente para productos bajo mínimo.
Response
{
  "alerts_created": 4,
  "timestamp": "2026-05-06T12:00:00",
  "message": "Created 4 new stock alerts"
}


SOLICITUDES LOGÍSTICAS

6. Solicitudes Pendientes
GET /solicitudes/pending
Obtiene solicitudes pendientes.
Response
[
  {
    "id": 1,
    "item_id": 2,
    "requested_quantity": 20,
    "reason": "restock",
    "priority": "high",
    "item_sku": "SKU-002",
    "item_name": "Monitor LG",
    "current_quantity": 1,
    "minimum_threshold": 5,
    "supplier_name": "TechSupply Inc"
  }
]


7. Solicitudes Aprobadas
GET /solicitudes/in-progress
Solicitudes aprobadas esperando entrega.
Response
[
  {
    "id": 5,
    "item_id": 3,
    "requested_quantity": 50,
    "reason": "restock",
    "approved_by": "admin",
    "approved_at": "2026-05-06T10:00:00",
    "item_sku": "SKU-003",
    "item_name": "Toner HP",
    "supplier_name": "Industrial Parts Ltd",
    "days_waiting": 2
  }
]


8. Solicitudes Completadas
GET /solicitudes/completed?days=7
Obtiene solicitudes completadas recientemente.
Query Params
Parámetro
Tipo
Descripción
days
int
Días hacia atrás

Response
[
  {
    "id": 9,
    "item_id": 1,
    "requested_quantity": 10,
    "reason": "restock",
    "fulfilled_at": "2026-05-05T18:00:00",
    "item_sku": "SKU-001",
    "item_name": "Laptop Dell"
  }
]


ÓRDENES DE COMPRA

9. Órdenes Pendientes
GET /purchase-orders/pending
Lista órdenes activas.
Response
[
  {
    "id": 11,
    "item_id": 2,
    "quantity": 25,
    "unit_price": 250.0,
    "total_amount": 6250.0,
    "status": "confirmed",
    "expected_delivery": "2026-05-10",
    "item_sku": "SKU-002",
    "item_name": "Monitor LG",
    "supplier_name": "TechSupply Inc"
  }
]


10. Órdenes Retrasadas
GET /purchase-orders/overdue
Obtiene órdenes vencidas.
Response
[
  {
    "id": 12,
    "item_id": 3,
    "quantity": 40,
    "expected_delivery": "2026-05-01",
    "days_overdue": 5,
    "item_sku": "SKU-003",
    "item_name": "Toner HP",
    "supplier_name": "Industrial Parts Ltd"
  }
]


ENTREGAS

11. Crear Entrega
POST /deliveries
Body
{
  "order_id": 1001,
  "delivery_address": "Av Reforma 123",
  "assigned_to": "Carlos",
  "vehicle": "CAM-01"
}

Response
{
  "id": 1,
  "status": "pending",
  "created_at": "2026-05-06T12:00:00"
}


12. Asignar Entrega
PATCH /deliveries/{delivery_id}/assign
Body
{
  "assigned_to": "Carlos",
  "vehicle": "CAM-01"
}

Response
{
  "id": 1,
  "assigned_to": "Carlos",
  "vehicle": "CAM-01"
}


13. Actualizar Estado de Entrega
PATCH /deliveries/{delivery_id}/status
Estados válidos
pending
in_transit
delivered
Body
{
  "status": "in_transit"
}

Response
{
  "id": 1,
  "status": "in_transit"
}


14. Obtener Entrega
GET /deliveries/{delivery_id}
Response
{
  "id": 1,
  "order_id": 1001,
  "delivery_address": "Av Reforma 123",
  "assigned_to": "Carlos",
  "vehicle": "CAM-01",
  "status": "delivered",
  "created_by": "admin",
  "created_at": "2026-05-06T10:00:00",
  "assigned_at": "2026-05-06T11:00:00",
  "delivered_at": "2026-05-06T14:00:00"
}


15. Listar Entregas
GET /deliveries
Response
[
  {
    "id": 1,
    "order_id": 1001,
    "delivery_address": "Av Reforma 123",
    "assigned_to": "Carlos",
    "vehicle": "CAM-01",
    "status": "delivered"
  }
]


Integración Recomendada
Inventario → Logística
Cuando inventario detecte:
quantity_on_hand < minimum_threshold

Debe invocar:
POST /monitor/check-and-alert


Compras → Inventario
Cuando compras confirme recepción:
purchase_order.status = received

Debe ejecutar actualización de stock.

Logística → Frontend
Dashboard recomendado:
Productos críticos
Alertas activas
Solicitudes pendientes
Entregas en tránsito
Órdenes vencidas

Estados Utilizados
Solicitudes
Estado
Significado
pending
Esperando aprobación
approved
Aprobada
fulfilled
Completada
rejected
Rechazada


Purchase Orders
Estado
Significado
pending
Pendiente
confirmed
Confirmada
shipped
En tránsito
received
Recibida
cancelled
Cancelada


Deliveries
Estado
Significado
pending
Pendiente
in_transit
En tránsito
delivered
Entregada


Recomendaciones de Producción
Recomendado implementar
JWT Authentication
API Gateway
Rate limiting
Retry policies
Structured logging
Prometheus metrics
Background workers
RabbitMQ/Kafka
SQL indexes
Pydantic validation
Row locking (FOR UPDATE)
Soft delete

Dependencias
pip install fastapi uvicorn psycopg[binary]


Ejecutar Servicio
uvicorn main:app --reload --port 8003


Variables de Entorno
POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/transactions_db

ALLOWED_ORIGINS=http://localhost:5173

ALLOW_CREDENTIALS=false


