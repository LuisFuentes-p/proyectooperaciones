Microservicio Finanzas — Guía de interacción
Descripción general
El microservicio Finanzas administra:
Usuarios internos del ERP
Roles y permisos
Acceso por áreas
Generación de reportes PDF financieros
Almacenamiento de reportes históricos
Descarga de reportes
Eliminación de reportes
Consulta de usuarios y permisos

URL Base
http://localhost:8000


Header requerido
La mayoría de endpoints requieren:
X-User-Name: admin

Ejemplo:
-H "X-User-Name: admin"


Roles disponibles
Rol
Permisos
admin
finanzas, compras, inventario, devoluciones, usuarios
compras
finanzas, compras
inventario
finanzas, inventario
auditor
finanzas, devoluciones
viewer
finanzas


Usuarios iniciales
Username
Nombre
Rol
admin
Administrador
admin
compras
Jefe de Compras
compras
inventario
Jefe de Inventario
inventario
auditor
Auditor Operativo
auditor
viewer
Consulta General
viewer


1. Health Check
Verificar estado del microservicio
Endpoint
GET /health

Ejemplo
curl http://localhost:8000/health

Respuesta
{
  "status": "ok"
}


2. Usuarios
Obtener usuario autenticado
Endpoint
GET /users/me

Ejemplo
curl -H "X-User-Name: admin" \
http://localhost:8000/users/me

Respuesta
{
  "id": 1,
  "username": "admin",
  "display_name": "Administrador",
  "role": "admin",
  "permissions": [
    "finanzas",
    "compras",
    "inventario",
    "devoluciones",
    "usuarios"
  ]
}


Obtener usuario por username
Endpoint
GET /users/{username}

Ejemplo
curl http://localhost:8000/users/admin


Obtener lista de usuarios
Endpoint
GET /users

Requiere permiso
usuarios

Ejemplo
curl -H "X-User-Name: admin" \
http://localhost:8000/users


3. Reportes financieros
Generar reporte de ingresos totales
Endpoint
POST /reports/ingresos-totales

Requiere permiso
finanzas

Ejemplo
curl -X POST \
-H "X-User-Name: admin" \
http://localhost:8000/reports/ingresos-totales

Qué hace
El endpoint:
genera un PDF financiero
almacena el PDF en PostgreSQL
registra metadata del reporte
devuelve información del archivo

Respuesta ejemplo
{
  "id": 1,
  "report_key": "ingresos_totales",
  "title": "Ingresos Totales",
  "filename": "ingresos_totales.pdf",
  "content_type": "application/pdf",
  "file_size": 15234
}


4. Tracking de reportes
Obtener historial de reportes
Endpoint
GET /reports/tracking

Ejemplo
curl -H "X-User-Name: admin" \
http://localhost:8000/reports/tracking

Respuesta
{
  "items": [
    {
      "id": 1,
      "report_key": "ingresos_totales",
      "title": "Ingresos Totales",
      "filename": "ingresos_totales.pdf",
      "content_type": "application/pdf",
      "file_size": 15234
    }
  ]
}


Descargar PDF de reporte
Endpoint
GET /reports/tracking/{report_id}/pdf

Ejemplo
curl -H "X-User-Name: admin" \
http://localhost:8000/reports/tracking/1/pdf \
--output ingresos.pdf


Eliminar reporte
Endpoint
DELETE /reports/tracking/{report_id}

Ejemplo
curl -X DELETE \
-H "X-User-Name: admin" \
http://localhost:8000/reports/tracking/1

Respuesta
{
  "deleted": true
}


5. Generar PDF directo
Obtener PDF temporal sin guardar
Endpoint
GET /reports/ingresos-totales/pdf

Ejemplo
curl http://localhost:8000/reports/ingresos-totales/pdf \
--output reporte.pdf

Nota
Este endpoint:
genera el PDF dinámicamente
NO lo almacena en base de datos

Contenido del reporte financiero
El PDF incluye:
Campo
Descripción
Descripción
Qué representa la métrica
Fuente de datos
Sistema origen
Eventos relacionados
Eventos Kafka o eventos de negocio
Frecuencia
Actualización
Fórmula
Cálculo financiero
Uso
Aplicación empresarial


Seguridad y permisos
Validación de usuarios
El sistema:
valida usuarios activos
valida permisos por área
bloquea accesos no autorizados

Errores comunes
Usuario faltante
{
  "detail": "Usuario requerido"
}


Usuario inexistente
{
  "detail": "Usuario no encontrado"
}


Sin permisos
{
  "detail": "No tiene permisos para esta area"
}


Reporte inexistente
{
  "detail": "Reporte no encontrado"
}


Flujo típico financiero
Flujo operativo
1. Usuario inicia sesión
2. Finanzas valida permisos
3. Usuario genera reporte
4. PDF se almacena en PostgreSQL
5. Sistema registra metadata
6. Usuario descarga reporte
7. Auditoría consulta historial


Base de datos
Tablas utilizadas
Tabla
Uso
app_users
Usuarios y roles
report_files
PDFs y metadata


Arquitectura financiera
Componentes principales
Frontend React
    ↓
FastAPI Finanzas
    ↓
PostgreSQL
    ↓
ReportLab PDF Engine


Puertos del ERP
Servicio
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
Frontend React/Vite
5173


