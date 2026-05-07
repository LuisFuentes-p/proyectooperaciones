Microservicio Compras — Guía de interacción
Descripción general
El microservicio Compras administra:
Proveedores
Clientes
Productos / inventario comercial
Órdenes de compra
Órdenes de venta
Pagos
Historial comercial
Generación de PDFs:
Órdenes de compra
Facturas de venta
Movimientos de stock automáticos

URL Base
http://localhost:8003


Header obligatorio
Todos los endpoints requieren:
user_name: admin

Ejemplo:
-H "user_name: admin"


1. Health Check
Verificar estado del microservicio
Endpoint
GET /health

Ejemplo
curl http://localhost:8003/health

Respuesta
{
  "status": "ok",
  "service": "compras"
}


2. Proveedores
Obtener proveedores
Endpoint
GET /suppliers

Ejemplo
curl -H "user_name: admin" \
http://localhost:8003/suppliers


Crear proveedor
Endpoint
POST /suppliers

Body
{
  "name": "Proveedor ABC",
  "contact_email": "ventas@abc.com",
  "phone": "5551234567",
  "address": "Calle Principal 123",
  "city": "CDMX",
  "country": "México"
}

Ejemplo
curl -X POST http://localhost:8003/suppliers \
-H "Content-Type: application/json" \
-H "user_name: admin" \
-d '{
  "name":"Proveedor ABC",
  "contact_email":"ventas@abc.com"
}'


3. Clientes
Obtener clientes
Endpoint
GET /customers

Ejemplo
curl -H "user_name: admin" \
http://localhost:8003/customers


Crear cliente
Endpoint
POST /customers

Body
{
  "name": "Cliente XYZ",
  "contact_email": "cliente@xyz.com",
  "phone": "5559876543",
  "customer_type": "retail",
  "credit_limit": 50000
}

Ejemplo
curl -X POST http://localhost:8003/customers \
-H "Content-Type: application/json" \
-H "user_name: admin" \
-d '{
  "name":"Cliente XYZ",
  "contact_email":"cliente@xyz.com",
  "credit_limit":50000
}'


4. Productos / Items
Obtener productos
Endpoint
GET /items

Ejemplo
curl -H "user_name: admin" \
http://localhost:8003/items


Obtener producto por ID
Endpoint
GET /items/{item_id}

Ejemplo
curl -H "user_name: admin" \
http://localhost:8003/items/1


Crear producto
Endpoint
POST /items

Body
{
  "sku": "SKU-100",
  "name": "Laptop Lenovo",
  "description": "Laptop empresarial",
  "quantity_on_hand": 10,
  "minimum_threshold": 5,
  "reorder_quantity": 20,
  "unit_cost": 12000,
  "unit_price": 15000,
  "unit_of_measure": "unidad",
  "supplier_id": 1,
  "category": "Electrónica"
}

Ejemplo
curl -X POST http://localhost:8003/items \
-H "Content-Type: application/json" \
-H "user_name: admin" \
-d '{
  "sku":"SKU-100",
  "name":"Laptop Lenovo",
  "quantity_on_hand":10,
  "unit_cost":12000,
  "unit_price":15000
}'


5. Órdenes de compra
Crear orden de compra
Endpoint
POST /purchase-orders

Body
{
  "item_id": 1,
  "supplier_id": 1,
  "quantity": 5,
  "unit_price": 1000,
  "expected_delivery_days": 7
}

Ejemplo
curl -X POST http://localhost:8003/purchase-orders \
-H "Content-Type: application/json" \
-H "user_name: admin" \
-d '{
  "item_id":1,
  "supplier_id":1,
  "quantity":5,
  "unit_price":1000
}'


Obtener órdenes de compra
Endpoint
GET /purchase-orders

Ejemplo
curl -H "user_name: admin" \
http://localhost:8003/purchase-orders


Obtener orden de compra por ID
Endpoint
GET /purchase-orders/{po_id}

Ejemplo
curl -H "user_name: admin" \
http://localhost:8003/purchase-orders/1


Descargar PDF de orden de compra
Endpoint
GET /purchase-orders/{po_id}/pdf

Ejemplo
curl -H "user_name: admin" \
http://localhost:8003/purchase-orders/1/pdf \
--output orden_compra.pdf


Actualizar estado de orden de compra
Estados válidos
pending
confirmed
shipped
received
cancelled
Endpoint
PATCH /purchase-orders/{po_id}/status

Ejemplo
curl -X PATCH \
"http://localhost:8003/purchase-orders/1/status?new_status=received" \
-H "user_name: admin"

Nota
Cuando el estado cambia a:
received

el stock aumenta automáticamente.

6. Órdenes de venta
Crear orden de venta
Endpoint
POST /sales-orders

Body
{
  "item_id": 1,
  "customer_id": 1,
  "quantity": 2,
  "expected_delivery_days": 3
}

Ejemplo
curl -X POST http://localhost:8003/sales-orders \
-H "Content-Type: application/json" \
-H "user_name: admin" \
-d '{
  "item_id":1,
  "customer_id":1,
  "quantity":2
}'

Nota
La orden:
reduce inventario automáticamente
genera factura PDF automáticamente

Obtener órdenes de venta
Endpoint
GET /sales-orders

Ejemplo
curl -H "user_name: admin" \
http://localhost:8003/sales-orders


Obtener orden de venta por ID
Endpoint
GET /sales-orders/{so_id}

Ejemplo
curl -H "user_name: admin" \
http://localhost:8003/sales-orders/1


Descargar factura PDF
Endpoint
GET /sales-orders/{so_id}/invoice

Ejemplo
curl -H "user_name: admin" \
http://localhost:8003/sales-orders/1/invoice \
--output factura.pdf


Actualizar estado de venta
Estados válidos
pending
confirmed
shipped
delivered
cancelled
Endpoint
PATCH /sales-orders/{so_id}/status

Ejemplo
curl -X PATCH \
"http://localhost:8003/sales-orders/1/status?new_status=delivered" \
-H "user_name: admin"

Nota
Si la orden se cancela:
cancelled

el stock se restaura automáticamente.

7. Pagos
Registrar pago de cliente
Endpoint
POST /payments/customer

Body
{
  "order_id": 1,
  "amount": 5000,
  "payment_method": "transfer",
  "notes": "Pago parcial"
}

Ejemplo
curl -X POST http://localhost:8003/payments/customer \
-H "Content-Type: application/json" \
-H "user_name: admin" \
-d '{
  "order_id":1,
  "amount":5000,
  "payment_method":"transfer"
}'


Registrar pago a proveedor
Endpoint
POST /payments/supplier

Ejemplo
curl -X POST http://localhost:8003/payments/supplier \
-H "Content-Type: application/json" \
-H "user_name: admin" \
-d '{
  "order_id":1,
  "amount":10000,
  "payment_method":"transfer"
}'


8. Historial comercial
Obtener historial de transacciones
Endpoint
GET /transactions/history

Ejemplo
curl -H "user_name: admin" \
http://localhost:8003/transactions/history


Filtros disponibles
Parámetro
Descripción
party_type
supplier/customer
party_name
nombre parcial
transaction_type
purchase/sale/payment
limit
límite de resultados


Ejemplo con filtros
curl -H "user_name: admin" \
"http://localhost:8003/transactions/history?transaction_type=sale"


9. Resumen comercial
Obtener estadísticas comerciales
Endpoint
GET /stats/commercial-summary

Ejemplo
curl -H "user_name: admin" \
http://localhost:8003/stats/commercial-summary


Flujo típico del sistema
Flujo de compras
1. Crear proveedor
2. Crear producto
3. Crear orden de compra
4. Confirmar recepción
5. Stock aumenta automáticamente
6. Registrar pago a proveedor


Flujo de ventas
1. Crear cliente
2. Crear orden de venta
3. Inventario disminuye automáticamente
4. Generar factura PDF
5. Entregar producto
6. Registrar pago del cliente


Puertos del ecosistema ERP
Microservicio
Puerto
Finanzas
8000
Inventario
8001
Logística
8002
Compras
8003
Autenticación
8004
Nómina
8006
Frontend Vite
5173

Compras
