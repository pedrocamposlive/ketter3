"""
Ketter 3.0 - PDF Report Generator
Professional transfer reports with triple SHA-256 verification

MRC: Simple, reliable PDF generation with all essential information
"""

from datetime import datetime
from io import BytesIO
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.models import Transfer, Checksum, AuditLog, ChecksumType


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable size"""
    if bytes_value == 0:
        return "0 Bytes"

    k = 1024
    sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    i = 0
    value = float(bytes_value)

    while value >= k and i < len(sizes) - 1:
        value /= k
        i += 1

    return f"{value:.2f} {sizes[i]}"


def format_datetime(dt: datetime) -> str:
    """Format datetime to readable string"""
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def get_status_color(status: str) -> colors.Color:
    """Get color for transfer status"""
    status_colors = {
        'completed': colors.green,
        'failed': colors.red,
        'cancelled': colors.grey,
        'pending': colors.orange,
        'validating': colors.blue,
        'copying': colors.blue,
        'verifying': colors.blue,
    }
    return status_colors.get(status.lower(), colors.black)


def generate_transfer_report(
    transfer: Transfer,
    checksums: List[Checksum],
    audit_logs: List[AuditLog]
) -> BytesIO:
    """
    Generate professional PDF report for a transfer

    Args:
        transfer: Transfer object
        checksums: List of checksum records (SOURCE, DESTINATION, FINAL)
        audit_logs: Complete audit trail

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )

    normal_style = styles['Normal']

    # === TITLE ===
    elements.append(Paragraph("KETTER 3.0", title_style))
    elements.append(Paragraph("File Transfer Verification Report", styles['Heading2']))
    elements.append(Spacer(1, 0.3*inch))

    # === REPORT METADATA ===
    report_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    elements.append(Paragraph(f"<b>Report Generated:</b> {report_time}", normal_style))
    elements.append(Paragraph(f"<b>Transfer ID:</b> #{transfer.id}", normal_style))
    elements.append(Spacer(1, 0.2*inch))

    # === TRANSFER SUMMARY ===
    elements.append(Paragraph("Transfer Summary", heading_style))

    summary_data = [
        ['File Name', transfer.file_name or 'N/A'],
        ['File Size', format_bytes(transfer.file_size or 0)],
        ['Status', transfer.status.value.upper()],
        ['Created', format_datetime(transfer.created_at)],
        ['Started', format_datetime(transfer.started_at)],
        ['Completed', format_datetime(transfer.completed_at)],
    ]

    summary_table = Table(summary_data, colWidths=[2*inch, 4.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.2*inch))

    # === FILE PATHS ===
    elements.append(Paragraph("File Paths", heading_style))

    path_data = [
        ['Source Path', transfer.source_path or 'N/A'],
        ['Destination Path', transfer.destination_path or 'N/A'],
    ]

    path_table = Table(path_data, colWidths=[2*inch, 4.5*inch])
    path_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(path_table)
    elements.append(Spacer(1, 0.2*inch))

    # === TRIPLE SHA-256 VERIFICATION ===
    elements.append(Paragraph("Triple SHA-256 Verification", heading_style))

    # Organize checksums by type
    checksum_map = {c.checksum_type: c for c in checksums}

    verification_data = [
        ['Type', 'SHA-256 Hash', 'Calculated At']
    ]

    for checksum_type in [ChecksumType.SOURCE, ChecksumType.DESTINATION, ChecksumType.FINAL]:
        if checksum_type in checksum_map:
            c = checksum_map[checksum_type]
            verification_data.append([
                checksum_type.value.upper(),
                c.checksum_value,
                format_datetime(c.calculated_at)
            ])

    verification_table = Table(verification_data, colWidths=[1.5*inch, 3.5*inch, 1.5*inch])
    verification_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        # Data rows
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Courier'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(verification_table)

    # Verification status
    source_hash = checksum_map.get(ChecksumType.SOURCE)
    dest_hash = checksum_map.get(ChecksumType.DESTINATION)

    if source_hash and dest_hash:
        if source_hash.checksum_value == dest_hash.checksum_value:
            verification_status = Paragraph(
                '<b><font color="green">✓ VERIFICATION PASSED: Checksums match exactly</font></b>',
                normal_style
            )
        else:
            verification_status = Paragraph(
                '<b><font color="red">✗ VERIFICATION FAILED: Checksums do not match</font></b>',
                normal_style
            )
        elements.append(Spacer(1, 0.1*inch))
        elements.append(verification_status)

    elements.append(Spacer(1, 0.2*inch))

    # === ERROR INFORMATION (if failed) ===
    if transfer.error_message:
        elements.append(Paragraph("Error Information", heading_style))
        error_text = Paragraph(
            f'<font color="red"><b>{transfer.error_message}</b></font>',
            normal_style
        )
        elements.append(error_text)
        elements.append(Spacer(1, 0.2*inch))

    # === AUDIT TRAIL ===
    elements.append(PageBreak())
    elements.append(Paragraph("Complete Audit Trail", heading_style))
    elements.append(Spacer(1, 0.1*inch))

    audit_data = [['#', 'Event Type', 'Message', 'Timestamp']]

    for idx, log in enumerate(audit_logs, 1):
        audit_data.append([
            str(idx),
            log.event_type.value.replace('_', ' ').upper(),
            log.message[:80] + ('...' if len(log.message) > 80 else ''),
            format_datetime(log.created_at)
        ])

    audit_table = Table(audit_data, colWidths=[0.4*inch, 1.3*inch, 3*inch, 1.8*inch])
    audit_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        # Data
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        # Alternate row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
    ]))
    elements.append(audit_table)

    # === FOOTER ===
    elements.append(Spacer(1, 0.4*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(
        "This report was automatically generated by Ketter 3.0 - File Transfer System with Triple SHA-256 Verification",
        footer_style
    ))
    elements.append(Paragraph(
        f"Report ID: KETTER-{transfer.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        footer_style
    ))

    # Build PDF
    doc.build(elements)

    # Get PDF from buffer
    buffer.seek(0)
    return buffer


def get_transfer_report_filename(transfer: Transfer) -> str:
    """Generate standardized filename for transfer report"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    safe_filename = (transfer.file_name or 'transfer').replace(' ', '_')[:50]
    return f"ketter_report_{safe_filename}_ID{transfer.id}_{timestamp}.pdf"
