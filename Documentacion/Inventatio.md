Inventario Microservice — Guía de Interacción
Descripción General
El microservicio de Inventario administra el catálogo de productos, niveles de stock, movimientos de inventario, alertas de stock y solicitudes logísticas.
Funcionalidades principales
Gestión de artículos de inventario (SKU, stock, umbrales mínimos)
Control de movimientos de stock
Solicitudes logísticas (reabastecimiento, devoluciones, daños)
Alertas automáticas de inventario
Integración con Compras para recepción de órdenes
Monitoreo de stock para Logística

Configuración Base
Base URL
http://localhost:8000

Headers requeridos
Todos los endpoints requieren el header:
user_name: nombre_usuario

Ejemplo:
user_name: admin

Si no se envía:
{
  "detail": "User not identified"
}


Health Check
Verificar estado del servicio
Endpoint
GET /health

Ejemplo
curl http://localhost:8000/health

Respuesta
{
  "status": "ok",
  "service": "inventario"
}


Gestión de Inventario
1. Listar artículos
Obtiene todos los productos registrados.
Endpoint
GET /items

Query Params opcionales
Parámetro
Tipo
Descripción
category
string
Filtrar por categoría
skip
int
Paginación inicial
limit
int
Cantidad máxima


Ejemplo
curl -X GET "http://localhost:8000/items?category=Electrónica" \
-H "user_name: admin"


Respuesta
[
  {
    "id": 1,
    "sku": "SKU-001",
    "name": "Laptop Dell XPS 13",
    "description": "High-performance laptop",
    "quantity_on_hand": 5,
    "minimum_threshold": 3,
    "reorder_quantity": 10,
    "unit_cost": 1200.0,
    "unit_of_measure": "unidad",
    "supplier_id": 1,
    "category": "Electrónica",
    "active": true,
    "last_updated": "2026-05-06T12:00:00",
    "below_minimum": false
  }
]


2. Obtener detalle de un artículo
Endpoint
GET /items/{item_id}

Ejemplo
curl -X GET http://localhost:8000/items/1 \
-H "user_name: admin"


Respuesta
{
  "id": 1,
  "sku": "SKU-001",
  "name": "Laptop Dell XPS 13",
  "quantity_on_hand": 5,
  "minimum_threshold": 3,
  "below_minimum": false
}


3. Actualizar stock
Permite aumentar o disminuir existencias.
Endpoint
POST /items/{item_id}/stock/update

Parámetros
Parámetro
Tipo
Descripción
quantity_change
int
Positivo o negativo
reason
string
Motivo del movimiento
reference_id
string
Referencia opcional


Ejemplo — Entrada de stock
curl -X POST "http://localhost:8000/items/1/stock/update?quantity_change=20&reason=restock&reference_id=PO-1001" \
-H "user_name: admin"


Ejemplo — Salida de stock
curl -X POST "http://localhost:8000/items/1/stock/update?quantity_change=-5&reason=sale&reference_id=SO-500" \
-H "user_name: admin"


Respuesta
{
  "item_id": 1,
  "new_quantity": 25,
  "change": 20
}


Solicitudes de Logística
Las solicitudes logísticas sirven para:
Reabastecimiento
Devoluciones
Reportes de daño
Ajustes de inventario

4. Crear solicitud logística
Endpoint
POST /solicitudes-logistica

Parámetros
Parámetro
Tipo
item_id
int
requested_quantity
int
reason
string
priority
string
notes
string


Prioridades válidas
low
normal
high
urgent


Ejemplo
curl -X POST "http://localhost:8000/solicitudes-logistica?item_id=1&requested_quantity=50&reason=restock&priority=high&notes=Stock%20critico" \
-H "user_name: admin"


Respuesta
{
  "id": 10,
  "item_id": 1,
  "requested_quantity": 50,
  "reason": "restock",
  "priority": "high",
  "status": "pending",
  "created_by": "admin",
  "created_at": "2026-05-06T12:00:00"
}


5. Listar solicitudes logísticas
Endpoint
GET /solicitudes-logistica

Query Params
Parámetro
Tipo
status
string
skip
int
limit
int


Ejemplo
curl "http://localhost:8000/solicitudes-logistica?status=pending" \
-H "user_name: admin"


Respuesta
[
  {
    "id": 10,
    "item_id": 1,
    "requested_quantity": 50,
    "reason": "restock",
    "status": "pending",
    "priority": "high"
  }
]


6. Aprobar solicitud logística
Endpoint
PATCH /solicitudes-logistica/{request_id}/approve

Ejemplo
curl -X PATCH http://localhost:8000/solicitudes-logistica/10/approve \
-H "user_name: admin"


Respuesta
{
  "id": 10,
  "status": "approved"
}


7. Completar solicitud logística
Endpoint
PATCH /solicitudes-logistica/{request_id}/fulfill

Ejemplo
curl -X PATCH http://localhost:8000/solicitudes-logistica/10/fulfill \
-H "user_name: admin"


Respuesta
{
  "id": 10,
  "status": "fulfilled",
  "item_id": 1,
  "requested_quantity": 50
}


Alertas de Stock
Las alertas permiten monitorear:
Bajo inventario
Stock agotado
Sobre inventario

8. Listar alertas de stock
Endpoint
GET /stock-alerts

Query Params
Parámetro
Tipo
unacknowledged_only
bool


Ejemplo
curl "http://localhost:8000/stock-alerts?unacknowledged_only=true" \
-H "user_name: admin"


Respuesta
[
  {
    "id": 1,
    "item_id": 1,
    "alert_type": "below_minimum",
    "current_quantity": 2,
    "threshold": 5,
    "severity": "critical",
    "acknowledged": false
  }
]


9. Reconocer alerta
Endpoint
POST /stock-alerts/{alert_id}/acknowledge

Ejemplo
curl -X POST http://localhost:8000/stock-alerts/1/acknowledge \
-H "user_name: admin"


Respuesta
{
  "id": 1,
  "acknowledged": true
}


Gestión de Proveedores
10. Listar proveedores
Endpoint
GET /suppliers


Ejemplo
curl http://localhost:8000/suppliers \
-H "user_name: admin"


Respuesta
[
  {
    "id": 1,
    "name": "TechSupply Inc",
    "contact_email": "sales@techsupply.com",
    "phone": "+1234567890",
    "city": "New York",
    "country": "USA",
    "active": true
  }
]


Integración con otros microservicios
Integración con Compras
Cuando Compras recibe una orden:
Compras → Inventario

Debe llamar:
POST /items/{item_id}/stock/update

Con:
quantity_change > 0
reason = purchase_received

Ejemplo:
curl -X POST "http://localhost:8000/items/1/stock/update?quantity_change=50&reason=purchase_received&reference_id=PO-3001" \
-H "user_name: compras"


Integración con Ventas
Cuando una venta es confirmada:
Ventas → Inventario

Debe descontarse stock:
curl -X POST "http://localhost:8000/items/1/stock/update?quantity_change=-2&reason=sale&reference_id=SO-9001" \
-H "user_name: ventas"


Integración con Logística
Logística consulta:
GET /stock-alerts

y crea solicitudes:
POST /solicitudes-logistica


Estados importantes
Estados de solicitudes logísticas
Estado
Descripción
pending
Pendiente
approved
Aprobada
fulfilled
Completada
rejected
Rechazada


Tipos de alertas
Tipo
Descripción
below_minimum
Bajo mínimo
stockout
Sin stock
overstock
Sobre stock


Tipos de movimiento
Tipo
Descripción
in
Entrada
out
Salida
adjustment
Ajuste
return
Devolución
damage
Daño


Flujo típico de operación
Reabastecimiento
1. Stock cae bajo mínimo
2. Se genera alerta
3. Logística crea solicitud
4. Solicitud aprobada
5. Compras genera orden de compra
6. Inventario recibe stock
7. Stock actualizado


Errores comunes
Usuario no identificado
{
  "detail": "User not identified"
}


Stock insuficiente
{
  "detail": "Insufficient stock"
}


Item no encontrado
{
  "detail": "Item not found"
}


Datos iniciales cargados automáticamente
El servicio crea automáticamente:
Proveedores de ejemplo
Productos demo
Tablas de inventario
Tablas de alertas
Tablas de movimientos
Todo ocurre en:
startup()


