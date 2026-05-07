Guía de Interacción — Microservicio Nómina
Descripción General
El microservicio de Nómina administra empleados, asistencia, cálculos salariales y pagos de nómina.
Funciones principales:
Registro de empleados
Control de asistencia
Cálculo automático de nómina
Historial de pagos
Consulta de información para auditoría
Base URL ejemplo:
http://localhost:8005

Header requerido en endpoints administrativos:
user_name: admin


Flujo General
1. Registrar empleado
2. Registrar asistencia
3. Ejecutar cálculo de nóina
4. Consultar historial de pagos


Endpoints

1. Health Check
Verifica que el servicio esté funcionando.
Request
GET /health

Response
{
  "status": "ok",
  "service": "nomina"
}


2. Registrar Empleado
Permite registrar nuevos empleados.
Request
POST /employees

Headers
user_name: admin

Body
{
  "employee_code": "EMP-001",
  "full_name": "Juan Pérez",
  "position": "Desarrollador Backend",
  "department": "Tecnología",
  "base_salary": 2500.00,
  "commission_rate": 5
}

Response
{
  "id": 1,
  "employee_code": "EMP-001",
  "full_name": "Juan Pérez",
  "position": "Desarrollador Backend",
  "department": "Tecnología",
  "base_salary": 2500.0,
  "commission_rate": 5.0,
  "active": true
}


3. Listar Empleados
Obtiene todos los empleados activos.
Request
GET /employees

Headers
user_name: admin

Response
[
  {
    "id": 1,
    "employee_code": "EMP-001",
    "full_name": "Juan Pérez",
    "position": "Desarrollador Backend",
    "department": "Tecnología",
    "base_salary": 2500.0,
    "commission_rate": 5.0,
    "active": true
  }
]


4. Registrar Asistencia
Registra asistencia diaria del empleado.
Request
POST /attendance

Headers
user_name: admin

Body
{
  "employee_id": 1,
  "date": "2026-05-06",
  "hours_worked": 8
}

Response
{
  "id": 1,
  "employee_id": 1,
  "date": "2026-05-06",
  "hours_worked": 8.0
}


5. Consultar Asistencia
Obtiene registros de asistencia.
Request
GET /attendance

Headers
user_name: admin

Response
[
  {
    "id": 1,
    "employee_id": 1,
    "date": "2026-05-06",
    "hours_worked": 8.0
  }
]


6. Ejecutar Nómina
Calcula pagos para un periodo.
Request
POST /payroll/run

Headers
user_name: admin

Body
{
  "employee_id": 1,
  "period": "2026-05"
}

Response
{
  "id": 1,
  "employee_id": 1,
  "period": "2026-05",
  "base_salary": 2500.0,
  "commission_amount": 125.0,
  "total_payment": 2625.0,
  "generated_at": "2026-05-06T18:00:00"
}


7. Historial de Nómina
Consulta pagos realizados.
Request
GET /payroll/history

Headers
user_name: admin

Response
[
  {
    "id": 1,
    "employee_id": 1,
    "period": "2026-05",
    "base_salary": 2500.0,
    "commission_amount": 125.0,
    "total_payment": 2625.0,
    "generated_at": "2026-05-06T18:00:00"
  }
]


Casos de Uso Cubiertos
HU-NOM-01
Registrar empleados.
Endpoints:
POST /employees
GET /employees


HU-NOM-02
Registrar asistencia.
Endpoints:
POST /attendance
GET /attendance


HU-NOM-03
Ejecutar cálculo de nómina.
Endpoint:
POST /payroll/run


HU-NOM-04
Consultar historial de pagos.
Endpoint:
GET /payroll/history


Flujo Completo de Ejemplo
1. Registrar empleado
POST /employees

↓
2. Registrar asistencia
POST /attendance

↓
3. Ejecutar nómina
POST /payroll/run

↓
4. Consultar historial
GET /payroll/history


Validaciones Importantes
Usuario requerido
Si no se envía header:
user_name

Respuesta:
{
  "detail": "User not identified"
}


Empleado inexistente
{
  "detail": "Employee not found"
}


Duplicado de empleado
{
  "detail": "Employee code already exists"
}


Integración con Otros Microservicios
Finanzas
Puede consumir información de pagos generados
Puede generar reportes financieros de nómina
Inventario
Independiente
Sin dependencia directa
Logística
Independiente
Sin dependencia directa
Compras
Independiente
Sin dependencia directa

Resumen
El microservicio de Nómina permite:
Gestionar empleados
Registrar asistencia
Automatizar pagos
Consultar historial salarial
Reducir errores manuales
Mantener trazabilidad y auditoría de pagos

