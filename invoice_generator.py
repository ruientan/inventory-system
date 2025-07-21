from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
import os
from datetime import datetime


def generate_invoice(items, to_location, moved_by):
    # ── file path ───────────────────────────────────────
    date_str = datetime.now().strftime("%d-%m-%Y")
    filename = f"invoice_{to_location}_{datetime.now().strftime('%d-%m-%Y_%H%M%S')}.pdf"
    filepath = os.path.join("static", "invoices", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)


    # ── doc setup ───────────────────────────────────────
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    elements, styles = [], getSampleStyleSheet()

    # ── invoice number / header ─────────────────────────
    prefix      = "HQ-M" if to_location.lower() == "mbella" else "HQ-C"
    invoice_no  = f"{prefix}-{datetime.now().strftime('%d%m%y')}"

    elements.extend([
        Paragraph("HQ #05-05", styles["Normal"]),
        Paragraph(f"Invoice&nbsp;No:&nbsp;<b>{invoice_no}</b>", styles["Normal"]),
        Paragraph("Stock Transfer Invoice", styles["Title"]),
        Paragraph(f"To:&nbsp;{to_location}", styles["Heading2"]),
        Paragraph(f"Date&nbsp;Issued:&nbsp;{date_str}", styles["Normal"]),
        Paragraph(f"Issued&nbsp;By:&nbsp;{moved_by}", styles["Normal"]),
        Spacer(1, 12),
    ])

    # ── table of items ──────────────────────────────────
    data = [["No.", "Product", "Quantity"]]
    for idx, (product, qty) in enumerate(items, start=1):
        data.append([str(idx), product, str(qty)])

    table = Table(data, colWidths=[40, 300, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
            [colors.whitesmoke, colors.whitesmoke]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 11),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
    ]))
    elements.extend([table, Spacer(1, 40)])

    # ── receiving & signatures ──────────────────────────
    elements.extend([
        Paragraph("Name&nbsp;(Receiving&nbsp;Party):&nbsp;__________________________", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Date:&nbsp;__________________________", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Signature&nbsp;(Receiving&nbsp;Party):&nbsp;____________________", styles["Normal"]),
        Spacer(1, 24),
        Paragraph(f"Signature&nbsp;(Issuer&nbsp;-&nbsp;{moved_by}):&nbsp;____________________", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Signature&nbsp;(Jane):&nbsp;____________________", styles["Normal"]),
    ])

    # ── build pdf ───────────────────────────────────────
    doc.build(elements)
    return filename
