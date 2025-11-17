"""
Ketter 3.0 - PDF Report Generator
Professional transfer reports with triple SHA-256 verification

MRC: Simple, reliable PDF generation with all essential information
Three-level report structure:
  - Level 1: Executive Summary (for managers)
  - Level 2: Technical Details + Recommendations (for IT)
  - Level 3: Complete Audit Trail (for compliance)
"""

from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import List, Tuple, Optional

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


def format_duration(seconds: float) -> str:
    """Format duration in seconds to readable format (1m 30s)"""
    if seconds is None:
        return "N/A"

    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def calculate_throughput(bytes_value: int, seconds: float) -> Tuple[float, str]:
    """Calculate throughput in MB/s"""
    if not seconds or seconds <= 0:
        return 0.0, "0.00 MB/s"

    mb_per_second = (bytes_value / (1024 * 1024)) / seconds
    return mb_per_second, f"{mb_per_second:.2f} MB/s"


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


def get_verification_status(checksums: List[Checksum]) -> Tuple[str, str]:
    """Determine verification status and message"""
    checksum_map = {c.checksum_type: c for c in checksums}

    source_hash = checksum_map.get(ChecksumType.SOURCE)
    dest_hash = checksum_map.get(ChecksumType.DESTINATION)

    if source_hash and dest_hash:
        if source_hash.checksum_value == dest_hash.checksum_value:
            return "PASSED", "Checksums match exactly - Data integrity verified"
        else:
            return "FAILED", "Checksums do not match - Data integrity compromised"

    return "UNKNOWN", "Checksums unavailable"


def generate_transfer_report(
    transfer: Transfer,
    checksums: List[Checksum],
    audit_logs: List[AuditLog]
) -> BytesIO:
    """
    Generate professional PDF report for a transfer
    Three-level structure in landscape format:
      - Level 1: Executive Summary (one page, manager-friendly)
      - Level 2: Technical Details + Recommendations (detailed analysis)
      - Level 3: Complete Audit Trail (compliance + compliance)

    Args:
        transfer: Transfer object
        checksums: List of checksum records (SOURCE, DESTINATION, FINAL)
        audit_logs: Complete audit trail

    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()

    # Create PDF document in Landscape format
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter[1::-1],  # Landscape: swap width and height
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.75*inch  # Extra space for footer
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    level_title_style = ParagraphStyle(
        'LevelTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    normal_style = styles['Normal']
    normal_style.fontSize = 9

    # Calculate metrics
    checksum_map = {c.checksum_type: c for c in checksums}
    verify_status, verify_message = get_verification_status(checksums)

    # Calculate duration and throughput
    duration_seconds = None
    throughput_mbps_val = 0.0
    throughput_str = "N/A"

    if transfer.started_at and transfer.completed_at:
        duration = transfer.completed_at - transfer.started_at
        duration_seconds = duration.total_seconds()
        throughput_mbps_val, throughput_str = calculate_throughput(
            transfer.file_size or 0,
            duration_seconds
        )

    duration_str = format_duration(duration_seconds) if duration_seconds else "N/A"

    # === PAGE 1: EXECUTIVE SUMMARY ===
    elements.append(Paragraph("KETTER 3.0 - Transfer Report", title_style))
    elements.append(Paragraph("Executive Summary", level_title_style))
    elements.append(Spacer(1, 0.1*inch))

    # Quick metrics table
    exec_summary_data = [
        ['File Name', transfer.file_name or 'N/A', 'Transfer ID', f"#{transfer.id}"],
        ['File Size', format_bytes(transfer.file_size or 0), 'Status', transfer.status.value.upper()],
        ['Duration', duration_str, 'Verification', verify_status],
        ['Throughput', throughput_str, 'Date', format_datetime(transfer.completed_at)],
    ]

    exec_table = Table(exec_summary_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2.5*inch])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    elements.append(exec_table)
    elements.append(Spacer(1, 0.12*inch))

    # Verification status highlight
    if verify_status == "PASSED":
        verify_color = "green"
        verify_icon = "[OK]"
    elif verify_status == "FAILED":
        verify_color = "red"
        verify_icon = "[FAIL]"
    else:
        verify_color = "orange"
        verify_icon = "[?]"

    elements.append(Paragraph(
        f'<b><font color="{verify_color}">{verify_icon} {verify_message}</font></b>',
        normal_style
    ))
    elements.append(Spacer(1, 0.15*inch))

    # === PAGE 2: TECHNICAL DETAILS ===
    elements.append(PageBreak())
    elements.append(Paragraph("Technical Details", level_title_style))
    elements.append(Spacer(1, 0.08*inch))

    # File paths
    elements.append(Paragraph("File Paths", heading_style))
    paths_data = [
        ['Source', transfer.source_path or 'N/A'],
        ['Destination', transfer.destination_path or 'N/A'],
    ]
    paths_table = Table(paths_data, colWidths=[1.2*inch, 6.3*inch])
    paths_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(paths_table)
    elements.append(Spacer(1, 0.1*inch))

    # Timing information
    elements.append(Paragraph("Timing Information", heading_style))
    timing_data = [
        ['Started', format_datetime(transfer.started_at), 'Completed', format_datetime(transfer.completed_at)],
        ['Duration', duration_str, 'Throughput', throughput_str],
    ]
    timing_table = Table(timing_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2.5*inch])
    timing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    elements.append(timing_table)
    elements.append(Spacer(1, 0.1*inch))

    # SHA-256 Verification
    elements.append(Paragraph("Triple SHA-256 Verification", heading_style))
    verification_data = [['Type', 'Hash Value', 'Calculated At']]

    for checksum_type in [ChecksumType.SOURCE, ChecksumType.DESTINATION, ChecksumType.FINAL]:
        if checksum_type in checksum_map:
            c = checksum_map[checksum_type]
            verification_data.append([
                checksum_type.value.upper(),
                c.checksum_value[:40] + '...',
                format_datetime(c.calculated_at)
            ])

    verification_table = Table(verification_data, colWidths=[1.2*inch, 3.5*inch, 2.3*inch])
    verification_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
    ]))
    elements.append(verification_table)
    elements.append(Spacer(1, 0.1*inch))

    # Recommendations
    elements.append(Paragraph("Recommendations", heading_style))
    if transfer.status.value == 'completed' and verify_status == "PASSED":
        rec_text = "Transfer completed successfully with verified data integrity. No action required."
    elif transfer.status.value == 'failed':
        rec_text = "Transfer failed. Review error information and retry or contact support."
    elif verify_status == "FAILED":
        rec_text = "Data integrity check failed. Do not use destination file. Investigate cause and retry."
    else:
        rec_text = "Transfer in progress or status unknown. Monitor for completion."

    elements.append(Paragraph(rec_text, normal_style))
    elements.append(Spacer(1, 0.08*inch))

    # Error information if present
    if transfer.error_message:
        elements.append(Paragraph("Error Information", heading_style))
        elements.append(Paragraph(
            f'<font color="red"><b>{transfer.error_message}</b></font>',
            normal_style
        ))
        elements.append(Spacer(1, 0.08*inch))

    # === PAGE 3: AUDIT TRAIL ===
    elements.append(PageBreak())
    elements.append(Paragraph("Complete Audit Trail", level_title_style))
    elements.append(Spacer(1, 0.1*inch))

    audit_data = [['#', 'Event Type', 'Message', 'Timestamp']]

    for idx, log in enumerate(audit_logs, 1):
        event_name = log.event_type.value.replace('_', ' ').upper()
        message = log.message
        audit_data.append([
            str(idx),
            event_name,
            message,
            format_datetime(log.created_at)
        ])

    # Audit table with better column sizing and text wrapping
    audit_table = Table(
        audit_data,
        colWidths=[0.5*inch, 1.8*inch, 4.2*inch, 1.5*inch]
    )
    audit_table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Data row styling
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),

        # Column alignment
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),

        # Grid and alternating colors
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),

        # Text wrapping
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(audit_table)

    # === FOOTER ===
    elements.append(Spacer(1, 0.3*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER
    )

    report_id = f"KETTER-{transfer.id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    elements.append(Paragraph(
        f"Report ID: {report_id} | Generated by Ketter 3.0 - File Transfer System",
        footer_style
    ))
    elements.append(Paragraph(
        "CONFIDENTIAL - This document is restricted to authorized personnel of the company. "
        "Unauthorized distribution is prohibited.",
        footer_style
    ))

    # Build PDF
    doc.build(elements)

    # Get PDF from buffer
    buffer.seek(0)
    return buffer


def get_transfer_report_filename(transfer: Transfer) -> str:
    """Generate standardized filename for transfer report"""
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    safe_filename = (transfer.file_name or 'transfer').replace(' ', '_')[:50]
    return f"ketter_report_{safe_filename}_ID{transfer.id}_{timestamp}.pdf"
