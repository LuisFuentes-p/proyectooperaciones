from io import BytesIO

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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

INCOME_METRIC = {
    'titulo': 'Ingresos Totales',
    'descripcion': 'Representa la suma total de ingresos generados por ventas en un periodo determinado.',
    'fuente': 'Microservicio de Ventas (pagos registrados, facturas emitidas).',
    'eventos': 'PaymentReceived, InvoiceCreated',
    'frecuencia': 'En tiempo real mediante eventos.',
    'formula': 'Suma de todos los pagos confirmados.',
    'uso': 'Permite medir el volumen de ingresos y evaluar el desempeno comercial.',
}


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


@app.get('/reports/ingresos-totales/pdf')
def ingresos_totales_pdf() -> Response:
    pdf_bytes = build_income_pdf()
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': 'inline; filename=ingresos_totales.pdf'},
    )
