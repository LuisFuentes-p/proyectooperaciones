from io import BytesIO
import os
from datetime import datetime
from typing import Any

from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import psycopg
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

app = FastAPI(title='Finanzas', version='0.1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

DATABASE_URL = os.getenv('POSTGRES_URL', os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/transactions_db'))
REPORT_FILENAME = 'ingresos_totales.pdf'
REPORT_KEY = 'ingresos_totales'
ROLE_PERMISSIONS = {
    'admin': ['finanzas', 'compras', 'inventario', 'devoluciones', 'usuarios'],
    'compras': ['finanzas', 'compras'],
    'inventario': ['finanzas', 'inventario'],
    'auditor': ['finanzas', 'devoluciones'],
    'viewer': ['finanzas'],
}
DEFAULT_USERS = [
    {'username': 'admin', 'display_name': 'Administrador', 'role': 'admin'},
    {'username': 'compras', 'display_name': 'Jefe de Compras', 'role': 'compras'},
    {'username': 'inventario', 'display_name': 'Jefe de Inventario', 'role': 'inventario'},
    {'username': 'auditor', 'display_name': 'Auditor Operativo', 'role': 'auditor'},
    {'username': 'viewer', 'display_name': 'Consulta General', 'role': 'viewer'},
]

INCOME_METRIC = {
    'titulo': 'Ingresos Totales',
    'descripcion': 'Representa la suma total de ingresos generados por ventas en un periodo determinado.',
    'fuente': 'Microservicio de Ventas (pagos registrados, facturas emitidas).',
    'eventos': 'PaymentReceived, InvoiceCreated',
    'frecuencia': 'En tiempo real mediante eventos.',
    'formula': 'Suma de todos los pagos confirmados.',
    'uso': 'Permite medir el volumen de ingresos y evaluar el desempeno comercial.',
}


def get_connection() -> psycopg.Connection[Any]:
    return psycopg.connect(DATABASE_URL)


def initialize_database() -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS report_files (
                    id BIGSERIAL PRIMARY KEY,
                    report_key TEXT NOT NULL,
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    file_bytes BYTEA NOT NULL,
                    file_size INTEGER NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                '''
            )
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS app_users (
                    id BIGSERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                '''
            )
            cursor.execute('SELECT COUNT(*) FROM app_users')
            user_count = cursor.fetchone()[0]
            if user_count == 0:
                for user in DEFAULT_USERS:
                    cursor.execute(
                        '''
                        INSERT INTO app_users (username, display_name, role, active)
                        VALUES (%s, %s, %s, TRUE)
                        ON CONFLICT (username) DO NOTHING
                        ''',
                        (user['username'], user['display_name'], user['role']),
                    )
        connection.commit()


def permissions_for_role(role: str) -> list[str]:
    return ROLE_PERMISSIONS.get(role, [])


def fetch_user_row(username: str) -> tuple[Any, ...] | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT id, username, display_name, role, active, created_at
                FROM app_users
                WHERE username = %s AND active = TRUE
                ''',
                (username,),
            )
            return cursor.fetchone()


def user_payload(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        'id': row[0],
        'username': row[1],
        'display_name': row[2],
        'role': row[3],
        'active': row[4],
        'created_at': row[5],
        'permissions': permissions_for_role(row[3]),
    }


def fetch_all_users() -> list[dict[str, Any]]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT id, username, display_name, role, active, created_at
                FROM app_users
                ORDER BY id ASC
                '''
            )
            rows = cursor.fetchall()

    return [user_payload(row) for row in rows]


def require_user(username: str | None, permission: str | None = None) -> dict[str, Any]:
    if not username:
        raise HTTPException(status_code=401, detail='Usuario requerido')

    row = fetch_user_row(username)
    if row is None:
        raise HTTPException(status_code=401, detail='Usuario no encontrado')

    payload = user_payload(row)
    if permission and permission not in payload['permissions']:
        raise HTTPException(status_code=403, detail='No tiene permisos para esta area')

    return payload


def persist_pdf_report(pdf_bytes: bytes) -> dict[str, Any]:
    created_at = datetime.utcnow()
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO report_files (report_key, title, filename, content_type, file_bytes, file_size)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
                ''',
                (
                    REPORT_KEY,
                    INCOME_METRIC['titulo'],
                    REPORT_FILENAME,
                    'application/pdf',
                    pdf_bytes,
                    len(pdf_bytes),
                ),
            )
            row = cursor.fetchone()
        connection.commit()

    if row is None:
        raise RuntimeError('No se pudo guardar el PDF')

    return {
        'id': row[0],
        'created_at': row[1] or created_at,
    }


def fetch_report_rows() -> list[dict[str, Any]]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT id, report_key, title, filename, content_type, file_size, created_at
                FROM report_files
                ORDER BY created_at DESC, id DESC
                '''
            )
            rows = cursor.fetchall()

    return [
        {
            'id': row[0],
            'report_key': row[1],
            'title': row[2],
            'filename': row[3],
            'content_type': row[4],
            'file_size': row[5],
            'created_at': row[6],
        }
        for row in rows
    ]


def fetch_report_pdf(report_id: int) -> tuple[bytes, str, str]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                SELECT file_bytes, filename, content_type
                FROM report_files
                WHERE id = %s
                ''',
                (report_id,),
            )
            row = cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail='Reporte no encontrado')

    return row[0], row[1], row[2]


def delete_report(report_id: int) -> bool:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM report_files WHERE id = %s', (report_id,))
            deleted_rows = cursor.rowcount
        connection.commit()

    return deleted_rows > 0


@app.on_event('startup')
def startup() -> None:
    initialize_database()


def build_income_pdf() -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'IncomeTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#111827'),
        spaceAfter=10,
    )
    label_style = ParagraphStyle(
        'Label',
        parent=styles['BodyText'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#374151'),
    )
    value_style = ParagraphStyle(
        'Value',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#111827'),
    )
    description_style = ParagraphStyle(
        'Description',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#374151'),
    )

    elements = [
        Paragraph('Reporte de Finanzas', styles['Heading2']),
        Paragraph(INCOME_METRIC['titulo'], title_style),
        Paragraph(
            'Documento estructurado para exponer una métrica financiera clave de forma clara y consumible.',
            description_style,
        ),
        Spacer(1, 14),
    ]

    rows = [
        ('Descripcion', INCOME_METRIC['descripcion']),
        ('Fuente de Datos', INCOME_METRIC['fuente']),
        ('Eventos Relacionados', INCOME_METRIC['eventos']),
        ('Frecuencia de Actualizacion', INCOME_METRIC['frecuencia']),
        ('Formula de Calculo', INCOME_METRIC['formula']),
        ('Uso en el Negocio', INCOME_METRIC['uso']),
    ]

    table_data = [[Paragraph('Campo', label_style), Paragraph('Detalle', label_style)]]
    for label, value in rows:
        table_data.append([Paragraph(label, label_style), Paragraph(value, value_style)])

    table = Table(table_data, colWidths=[5.1 * cm, 10.2 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
                ('GRID', (0, 0), (-1, -1), 0.6, colors.HexColor('#d1d5db')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]
        )
    )

    elements.append(table)
    elements.append(Spacer(1, 16))
    elements.append(
        Paragraph(
            'Fuente conceptual: microservicio de ventas, con actualizacion basada en eventos para mantener consistencia operacional.',
            description_style,
        )
    )

    document.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.get('/users/me')
def read_current_user(x_user_name: str | None = Header(default=None, alias='X-User-Name')) -> dict[str, Any]:
    return require_user(x_user_name)


@app.get('/users/{username}')
def get_user_by_username(username: str) -> dict[str, Any]:
    """Get user by username - for initial user load"""
    row = fetch_user_row(username)
    if row is None:
        raise HTTPException(status_code=401, detail='Usuario no encontrado')
    return user_payload(row)


@app.get('/users')
def list_users(x_user_name: str | None = Header(default=None, alias='X-User-Name')) -> dict[str, list[dict[str, Any]]]:
    require_user(x_user_name, 'usuarios')
    return {'items': fetch_all_users()}


@app.post('/reports/ingresos-totales')
def create_ingresos_totales_report(x_user_name: str | None = Header(default=None, alias='X-User-Name')) -> dict[str, Any]:
    require_user(x_user_name, 'finanzas')
    pdf_bytes = build_income_pdf()
    persisted_report = persist_pdf_report(pdf_bytes)
    return {
        'id': persisted_report['id'],
        'report_key': REPORT_KEY,
        'title': INCOME_METRIC['titulo'],
        'filename': REPORT_FILENAME,
        'content_type': 'application/pdf',
        'file_size': len(pdf_bytes),
        'created_at': persisted_report['created_at'],
    }


@app.get('/reports/tracking')
def list_reports(x_user_name: str | None = Header(default=None, alias='X-User-Name')) -> dict[str, list[dict[str, Any]]]:
    require_user(x_user_name, 'finanzas')
    return {'items': fetch_report_rows()}


@app.get('/reports/tracking/{report_id}/pdf')
def read_report_pdf(report_id: int, x_user_name: str | None = Header(default=None, alias='X-User-Name')) -> Response:
    require_user(x_user_name, 'finanzas')
    pdf_bytes, filename, content_type = fetch_report_pdf(report_id)
    return Response(
        content=pdf_bytes,
        media_type=content_type,
        headers={'Content-Disposition': f'inline; filename={filename}'},
    )


@app.delete('/reports/tracking/{report_id}')
def remove_report(report_id: int, x_user_name: str | None = Header(default=None, alias='X-User-Name')) -> dict[str, bool]:
    require_user(x_user_name, 'finanzas')
    deleted = delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Reporte no encontrado')
    return {'deleted': True}


@app.get('/reports/ingresos-totales/pdf')
def ingresos_totales_pdf() -> Response:
    pdf_bytes = build_income_pdf()
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': 'inline; filename=ingresos_totales.pdf'},
    )
