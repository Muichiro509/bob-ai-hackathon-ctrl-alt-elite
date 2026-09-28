"""
generate_dummy_pdfs.py
──────────────────────
Generates realistic dummy PDF documents for testing the
AI-Powered Document Forgery Detection Assistant.

Document types produced
  1. COVID Vaccination Certificate   (genuine + forged)
  2. University Degree Certificate   (genuine + forged)
  3. Property Sale Deed              (genuine + forged)
  4. First Information Report (FIR)  (genuine + forged)

Forged variants contain intentional anomalies:
  • Font inconsistencies / mixed typefaces
  • Altered dates / numeric fields
  • Misaligned or missing official seals / watermarks
  • Suspicious metadata (wrong creation date, blank author)
  • Signature placeholder irregularities

Run:
    python src/generate_dummy_pdfs.py
Output: demo/sample_documents/
"""

import os
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "demo", "sample_documents")
os.makedirs(OUT_DIR, exist_ok=True)

W, H = A4          # 595.27 x 841.89 points


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _base_styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("Center14",   parent=s["Normal"], fontSize=14, alignment=TA_CENTER, spaceAfter=6))
    s.add(ParagraphStyle("Center12",   parent=s["Normal"], fontSize=12, alignment=TA_CENTER, spaceAfter=4))
    s.add(ParagraphStyle("Center10",   parent=s["Normal"], fontSize=10, alignment=TA_CENTER, spaceAfter=4))
    s.add(ParagraphStyle("Bold16",     parent=s["Normal"], fontSize=16, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=8))
    s.add(ParagraphStyle("Bold14",     parent=s["Normal"], fontSize=14, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=6))
    s.add(ParagraphStyle("Bold12",     parent=s["Normal"], fontSize=12, fontName="Helvetica-Bold", alignment=TA_LEFT,   spaceAfter=4))
    s.add(ParagraphStyle("Small9",     parent=s["Normal"], fontSize=9,  alignment=TA_LEFT,   spaceAfter=2))
    s.add(ParagraphStyle("SmallC9",    parent=s["Normal"], fontSize=9,  alignment=TA_CENTER, spaceAfter=2))
    s.add(ParagraphStyle("Justify11",  parent=s["Normal"], fontSize=11, alignment=TA_JUSTIFY, spaceAfter=6, leading=16))
    s.add(ParagraphStyle("Right10",    parent=s["Normal"], fontSize=10, alignment=TA_RIGHT,  spaceAfter=4))
    return s


def _watermark(c: canvas.Canvas, text: str, color=colors.Color(0.85, 0.85, 0.85, 0.4)):
    c.saveState()
    c.setFont("Helvetica-Bold", 52)
    c.setFillColor(color)
    c.translate(W / 2, H / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, text)
    c.restoreState()


def _border(c: canvas.Canvas, forged=False):
    c.saveState()
    c.setLineWidth(2 if not forged else 1)          # forged = thinner border
    c.setStrokeColor(colors.darkblue if not forged else colors.Color(0.3, 0.3, 0.3))
    margin = 20
    c.rect(margin, margin, W - 2 * margin, H - 2 * margin)
    if not forged:
        c.setLineWidth(0.5)
        c.rect(margin + 4, margin + 4, W - 2 * margin - 8, H - 2 * margin - 8)
    c.restoreState()


def _seal(c: canvas.Canvas, x, y, r=28, label="GOVT. OF INDIA", forged=False):
    """Draw a simple circular seal; forged version is misaligned / faded."""
    c.saveState()
    alpha = 0.15 if forged else 0.30
    c.setFillColor(colors.Color(0, 0, 0.6, alpha))
    c.setStrokeColor(colors.Color(0, 0, 0.6, alpha * 2))
    c.setLineWidth(1.5)
    c.circle(x, y, r, stroke=1, fill=1)
    c.setFont("Helvetica-Bold", 6 if not forged else 5)
    c.setFillColor(colors.Color(1, 1, 1, 0.9))
    c.drawCentredString(x, y + 2, label)
    c.drawCentredString(x, y - 6, "★ OFFICIAL ★" if not forged else "★ OFFIC1AL ★")   # typo in forged
    c.restoreState()


def _sig_block(c: canvas.Canvas, x, y, name, title, forged=False):
    c.saveState()
    c.setFont("Helvetica-Oblique" if not forged else "Courier-Oblique", 10)
    c.setFillColor(colors.black)
    # Genuine: a smooth curve; forged: just a straight scribble
    if not forged:
        p = c.beginPath()
        p.moveTo(x, y)
        p.curveTo(x + 10, y + 8, x + 30, y + 12, x + 55, y + 4)
        p.curveTo(x + 65, y, x + 70, y - 4, x + 80, y - 2)
        c.drawPath(p, stroke=1, fill=0)
    else:
        c.line(x, y + 4, x + 80, y + 4)      # flat line — suspicious
    c.setFont("Helvetica", 8)
    c.drawString(x, y - 10, name)
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(x, y - 20, title)
    c.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# 1. COVID Vaccination Certificate
# ─────────────────────────────────────────────────────────────────────────────

def _covid_cert(path: str, forged: bool):
    c = canvas.Canvas(path, pagesize=A4)
    if forged:
        c.setAuthor("")                      # blank author — metadata anomaly
        # forged doc intentionally has no title set (metadata anomaly)
    else:
        c.setAuthor("Ministry of Health & Family Welfare, Government of India")
        c.setTitle("COVID-19 Vaccination Certificate")

    _border(c, forged)
    if not forged:
        _watermark(c, "VERIFIED")
    else:
        _watermark(c, "VERIFIED", color=colors.Color(0.92, 0.92, 0.92, 0.2))

    # Header band
    c.setFillColor(colors.Color(0.05, 0.27, 0.53))
    c.rect(20, H - 100, W - 40, 70, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.white)
    c.drawCentredString(W / 2, H - 60, "Government of India")
    c.setFont("Helvetica", 11)
    c.drawCentredString(W / 2, H - 78, "Ministry of Health & Family Welfare — CoWIN Portal")

    # Title
    c.setFont("Helvetica-Bold", 22 if not forged else 20)
    c.setFillColor(colors.Color(0.05, 0.27, 0.53))
    c.drawCentredString(W / 2, H - 135, "COVID-19 VACCINATION CERTIFICATE")

    # Beneficiary details table
    data = [
        ["Beneficiary Name",  "Rahul Kumar Sharma"  if not forged else "Rahul  Kumar  Sharrna"],
        ["Date of Birth",     "15-Aug-1989"         if not forged else "15-Aug-1989"],
        ["Gender",            "Male"],
        ["Beneficiary Ref. No.", "9182736450817263"],
        ["Vaccine",           "COVISHIELD (AstraZeneca)"  if not forged else "C0VISHIELD (AstraZeneca)"],   # zero not O
        ["Dose",              "2nd Dose"],
        ["Vaccination Date",  "22-Mar-2021"         if not forged else "22-Mar-2O21"],   # O instead of 0
        ["Vaccination Center","Primary Health Centre, Sector 12, Gurugram, Haryana"],
        ["Next Dose Due",     "N/A (Fully Vaccinated)"],
        ["Verifiable QR",     "[QR CODE PLACEHOLDER]"],
    ]

    font_name = "Helvetica" if not forged else "Courier"      # font inconsistency in forged
    col_widths = [160, 320]
    table = Table(data, colWidths=col_widths)
    ts = TableStyle([
        ("FONT",        (0, 0), (0, -1), "Helvetica-Bold", 10),
        ("FONT",        (1, 0), (1, -1), font_name, 10),
        ("BACKGROUND",  (0, 0), (-1, 0), colors.Color(0.9, 0.93, 0.97)),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.Color(0.96, 0.97, 1)]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ])
    table.setStyle(ts)

    # Draw table
    table_w = sum(col_widths)
    x_start = (W - table_w) / 2
    table.wrapOn(c, table_w, H)
    table.drawOn(c, x_start, H - 430)

    # Seal & signature
    _seal(c, 100, 210, label="MoHFW\nGOVT.", forged=forged)
    _sig_block(c, 350, 230, "Dr. R. S. Sharma, IAS", "Director General of Health Services", forged=forged)

    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    c.drawCentredString(W / 2, 40,
        "This certificate is digitally generated. Verify at cowin.gov.in | Helpline: 1075")
    if forged:
        c.setFont("Courier", 7)
        c.setFillColor(colors.Color(0.6, 0, 0))
        c.drawCentredString(W / 2, 28, "[DOCUMENT CONTAINS ANOMALIES — FOR FORENSIC TESTING ONLY]")

    c.save()


# ─────────────────────────────────────────────────────────────────────────────
# 2. University Degree Certificate
# ─────────────────────────────────────────────────────────────────────────────

def _degree_cert(path: str, forged: bool):
    c = canvas.Canvas(path, pagesize=A4)
    if forged:
        c.setAuthor("")
        c.setProducer("Unknown")
    else:
        c.setAuthor("Registrar, University of Delhi")
        c.setTitle("Bachelor of Technology — Degree Certificate")

    _border(c, forged)
    if not forged:
        _watermark(c, "UNIVERSITY OF DELHI")
    else:
        _watermark(c, "UNIVERSITY OF DELHI", color=colors.Color(0.92, 0.92, 0.92, 0.15))

    # University crest area
    c.setFillColor(colors.Color(0.5, 0.1, 0.1))
    c.rect(20, H - 90, W - 40, 60, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.white)
    c.drawCentredString(W / 2, H - 52, "UNIVERSITY OF DELHI")
    c.setFont("Helvetica", 10)
    c.drawCentredString(W / 2, H - 68, "Estd. 1922  •  NAAC Grade A++  •  Delhi — 110007")

    # Certificate body
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.Color(0.5, 0.1, 0.1))
    c.drawCentredString(W / 2, H - 115, "DEGREE CERTIFICATE")

    body_x = 60
    line_y = H - 155
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    c.drawString(body_x, line_y,
        "This is to certify that")

    name_font = "Helvetica-BoldOblique" if not forged else "Times-BoldItalic"  # font inconsistency
    c.setFont(name_font, 18)
    c.setFillColor(colors.Color(0.1, 0.1, 0.5))
    c.drawCentredString(W / 2, line_y - 30,
        "Priya Nandkumar Joshi" if not forged else "Priya Nandkumar J0shi")   # zero anomaly

    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    lines = [
        f"D/O Shri Nandkumar Joshi, having passed the prescribed examinations of this University",
        f"with {'First Class with Distinction' if not forged else 'First  Class  with  Distinction'} in the year "
        f"{'2022' if not forged else '2O22'} is hereby",   # year tamper
        "awarded the degree of",
    ]
    y = line_y - 60
    for ln in lines:
        c.drawCentredString(W / 2, y, ln)
        y -= 18

    c.setFont("Helvetica-Bold", 15 if not forged else 14)
    c.setFillColor(colors.Color(0.5, 0.1, 0.1))
    c.drawCentredString(W / 2, y - 10, "BACHELOR OF TECHNOLOGY")
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    c.drawCentredString(W / 2, y - 28,
        "in Computer Science & Engineering")

    y -= 60
    details = [
        ["Enrollment No.",    "DU/2018/CSE/04712"],
        ["Roll No.",          "18021556009"       if not forged else "18O21556OO9"],   # O/0 substitution
        ["Division",          "First Class with Distinction"],
        ["CGPA",              "9.1 / 10.0"        if not forged else "9.8 / 10.0"],   # score tampered
        ["Date of Issue",     "15-Jun-2022"       if not forged else "15-Jun-2022"],
        ["Certificate No.",   "DU/2022/BTech/04712/C"],
    ]
    table = Table(details, colWidths=[160, 280])
    table.setStyle(TableStyle([
        ("FONT",       (0, 0), (0, -1), "Helvetica-Bold", 10),
        ("FONT",       (1, 0), (1, -1), "Helvetica" if not forged else "Courier", 10),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.Color(0.7, 0.7, 0.7)),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.Color(0.97, 0.95, 0.95)]),
        ("LEFTPADDING",(0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    table_w = 160 + 280
    table.wrapOn(c, table_w, H)
    table.drawOn(c, (W - table_w) / 2, y - 120)

    # Seal & signatures
    _seal(c, 100, 190, label="Univ. of\nDelhi", forged=forged)
    _sig_block(c, 200, 175, "Prof. A. K. Mishra", "Registrar, University of Delhi", forged=forged)
    _sig_block(c, 390, 175, "Prof. S. R. Gupta", "Dean of Examinations", forged=forged)

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    c.drawCentredString(W / 2, 40, "Verify this certificate at https://verify.du.ac.in | Ref: DU/2022/BTech/04712/C")
    if forged:
        c.setFont("Courier", 7)
        c.setFillColor(colors.Color(0.6, 0, 0))
        c.drawCentredString(W / 2, 28, "[DOCUMENT CONTAINS ANOMALIES — FOR FORENSIC TESTING ONLY]")

    c.save()


# ─────────────────────────────────────────────────────────────────────────────
# 3. Property Sale Deed
# ─────────────────────────────────────────────────────────────────────────────

def _property_deed(path: str, forged: bool):
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
        topMargin=2.5 * cm, bottomMargin=2 * cm,
    )
    s = _base_styles()
    story = []

    # Header
    story.append(Paragraph("<b>OFFICE OF THE SUB-REGISTRAR</b>", s["Bold16"]))
    story.append(Paragraph("District — South West Delhi, State — Delhi", s["Center12"]))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("<b>SALE DEED</b>", s["Bold16"]))
    story.append(Paragraph(
        f"Document No.: <b>SRO/SWD/{'2023' if not forged else '2O23'}/08/004712</b>"
        f"  &nbsp;&nbsp;  Registered On: <b>{'14-Aug-2023' if not forged else '14-Aug-2023'}</b>",
        s["Center12"]))
    story.append(Spacer(1, 0.4 * cm))

    # Parties
    story.append(Paragraph("<b>PARTIES TO THIS DEED</b>", s["Bold12"]))
    seller_name = "Shri Ramesh Chandra Agarwal" if not forged else "Shri Ramesh  Chandra Agrawal"
    buyer_name  = "Smt. Sunita Devendra Mehta"
    story.append(Paragraph(
        f"<b>Seller (Transferor):</b> {seller_name}, S/O Late Shri Mohan Lal Agarwal, "
        f"R/O House No. 42, Block-C, Dwarka Sector 7, New Delhi — 110075. "
        f"Aadhaar: {'XXXX-XXXX-4521' if not forged else 'XXXX-XXXX-4521'}.",
        s["Justify11"]))
    story.append(Paragraph(
        f"<b>Buyer (Transferee):</b> {buyer_name}, W/O Shri Devendra Mehta, "
        f"R/O Flat 302, Green Valley Apartments, Sector 23, Dwarka, New Delhi — 110077. "
        f"Aadhaar: XXXX-XXXX-7832.",
        s["Justify11"]))
    story.append(Spacer(1, 0.3 * cm))

    # Property description
    story.append(Paragraph("<b>PROPERTY DESCRIPTION</b>", s["Bold12"]))
    story.append(Paragraph(
        f"Plot No. 42, Block-C, Dwarka Sector 7, New Delhi — 110075. "
        f"Area: <b>{'120 sq. yards' if not forged else '150 sq. yards'}</b> "   # area altered
        f"({'1080 sq. ft.' if not forged else '1350 sq. ft.'}). "
        f"Bounded: North — Road 12 m; South — Plot No. 41; East — Plot No. 43; West — Park.",
        s["Justify11"]))
    story.append(Spacer(1, 0.3 * cm))

    # Consideration
    story.append(Paragraph("<b>CONSIDERATION AMOUNT</b>", s["Bold12"]))
    amount_words = "Seventy-Five Lakhs Only" if not forged else "Ninety Lakhs Only"
    amount_num   = "₹ 75,00,000/-"           if not forged else "₹ 90,00,000/-"
    story.append(Paragraph(
        f"The total sale consideration is <b>{amount_num}</b> (Rupees {amount_words}), "
        f"paid by the Buyer to the Seller in full prior to registration of this deed, "
        f"the receipt of which is hereby acknowledged.",
        s["Justify11"]))
    story.append(Spacer(1, 0.3 * cm))

    # Stamp duty
    story.append(Paragraph("<b>STAMP DUTY & REGISTRATION FEE</b>", s["Bold12"]))
    stamp = "₹ 4,50,000/-" if not forged else "₹ 5,40,000/-"
    reg   = "₹ 75,000/-"   if not forged else "₹ 90,000/-"
    story.append(Paragraph(
        f"Stamp Duty Paid: <b>{stamp}</b>  |  Registration Fee: <b>{reg}</b>  |  "
        f"e-Challan No.: {'DL2308140047' if not forged else 'DL23O814OO47'}.",  # O/0
        s["Justify11"]))
    story.append(Spacer(1, 0.4 * cm))

    # Witnesses
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("<b>WITNESSES</b>", s["Bold12"]))
    witnesses = [
        ["1. Shri Vijay Kumar Sharma",  "R/O 15, Vasant Kunj, New Delhi",    "Aadhaar: XXXX-XXXX-1234"],
        ["2. Smt. Kamla Devi Verma",    "R/O 88, Rohini Sector 3, New Delhi", "Aadhaar: XXXX-XXXX-5678"],
    ]
    wt = Table(witnesses, colWidths=[160, 180, 140])
    wt.setStyle(TableStyle([
        ("FONT",   (0, 0), (-1, -1), "Helvetica" if not forged else "Courier", 9),
        ("GRID",   (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(wt)
    story.append(Spacer(1, 0.5 * cm))

    # Signature blocks
    sig_data = [
        ["Signature of Seller", "", "Signature of Buyer"],
        ["____________________", "", "____________________"],
        [seller_name, "", buyer_name],
        ["", "", ""],
        ["Sub-Registrar's Seal & Signature", "", ""],
        ["____________________", "", ""],
        ["Sub-Registrar, SRO South-West Delhi", "", ""],
    ]
    st = Table(sig_data, colWidths=[180, 60, 240])
    st.setStyle(TableStyle([
        ("FONT",   (0, 0), (-1, -1), "Helvetica" if not forged else "Courier", 9),
        ("FONT",   (0, 1), (0, 1),   "Helvetica-Bold", 9),
        ("ALIGN",  (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(st)

    if forged:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(
            "<font color='red' size='7'>[DOCUMENT CONTAINS ANOMALIES — FOR FORENSIC TESTING ONLY]</font>",
            s["Center10"]))

    doc.build(story)


# ─────────────────────────────────────────────────────────────────────────────
# 4. First Information Report (FIR)
# ─────────────────────────────────────────────────────────────────────────────

def _fir(path: str, forged: bool):
    c = canvas.Canvas(path, pagesize=A4)
    if forged:
        c.setAuthor("")
        c.setProducer("PDF Writer 2.0")
    else:
        c.setAuthor("Delhi Police — FIR Management System")
        c.setTitle("First Information Report")

    _border(c, forged)
    if not forged:
        _watermark(c, "DELHI POLICE")

    # Header
    c.setFillColor(colors.Color(0.07, 0.17, 0.37))
    c.rect(20, H - 95, W - 40, 65, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 17)
    c.setFillColor(colors.white)
    c.drawCentredString(W / 2, H - 50, "DELHI POLICE")
    c.setFont("Helvetica", 10)
    c.drawCentredString(W / 2, H - 65, "First Information Report (FIR)")
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, H - 80, "Under Section 154 Cr.P.C.")

    # FIR details
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.Color(0.07, 0.17, 0.37))
    c.drawCentredString(W / 2, H - 115, "FIRST INFORMATION REPORT")

    margin_l = 50
    y = H - 145
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)

    fir_data = [
        ("FIR No.",              f"{'2024/01/0473' if not forged else '2024/01/O473'}"),   # O/0
        ("Police Station",       "Dwarka Sector 7, South-West Delhi"),
        ("District",             "South West Delhi"),
        ("Date of FIR",          f"{'07-Jan-2024' if not forged else '07-Jan-2O24'}"),     # O/0
        ("Time of FIR",          "14:35 Hrs"),
        ("Date of Occurrence",   f"{'06-Jan-2024' if not forged else '06-Jan-2O24'}"),
        ("Time of Occurrence",   "22:10 – 22:45 Hrs"),
        ("Place of Occurrence",  "Plot No. 42, Block-C, Dwarka Sector 7, New Delhi"),
        ("IPC Sections",         "420, 406, 34 IPC" if not forged else "420, 406, 34 lPC"),  # l vs I
        ("Complainant",          "Shri Ramesh Chandra Agarwal"),
        ("Father/Husband",       "Late Shri Mohan Lal Agarwal"),
        ("Address",              "House No. 42, Block-C, Dwarka Sector 7, New Delhi — 110075"),
        ("Mobile",               "98XXXXXXXX"),
        ("Accused (Known)",      f"{'Shri Suresh Gupta' if not forged else 'Shri Suresh  Gupta'}, R/O Unknown"),
    ]

    font_val = "Helvetica" if not forged else "Courier"
    for label, value in fir_data:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margin_l, y, f"{label}:")
        c.setFont(font_val, 9)
        c.drawString(margin_l + 140, y, value)
        y -= 17

    # Complaint text
    y -= 8
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin_l, y, "Brief Facts / Gist of FIR:")
    y -= 14
    c.setFont("Helvetica" if not forged else "Courier", 9)
    gist = (
        "The complainant states that on 06-Jan-2024 at approximately 22:10 hrs, "
        "the accused Shri Suresh Gupta, in conspiracy with unknown persons, fraudulently "
        "executed a forged Sale Deed bearing Document No. SRO/SWD/2023/08/004712 by "
        "impersonating the complainant using a fabricated Aadhaar card and forged signatures. "
        "The property at Plot No. 42, Block-C, Dwarka Sector 7 was illegally transferred without "
        "the knowledge or consent of the complainant. The complainant prays that the FIR be "
        "registered and appropriate legal action be initiated forthwith."
    )
    # Word-wrap manually
    words = gist.split()
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if c.stringWidth(test, "Helvetica", 9) < (W - 2 * margin_l):
            line = test
        else:
            c.drawString(margin_l, y, line)
            y -= 13
            line = w
    if line:
        c.drawString(margin_l, y, line)
        y -= 13

    # Officer & seal
    y -= 15
    _seal(c, margin_l + 30, y - 10, label="Delhi\nPolice", forged=forged)
    _sig_block(c, 300, y + 10, "Insp. Rajeev Nair (Badge: 4721)", "Station House Officer, PS Dwarka Sec 7", forged=forged)

    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.grey)
    c.drawCentredString(W / 2, 38,
        "This FIR is registered under Section 154 Cr.P.C. | Delhi Police FIR Portal: delhipolice.gov.in")
    if forged:
        c.setFont("Courier", 7)
        c.setFillColor(colors.Color(0.6, 0, 0))
        c.drawCentredString(W / 2, 26, "[DOCUMENT CONTAINS ANOMALIES — FOR FORENSIC TESTING ONLY]")

    c.save()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

DOCS = [
    ("covid_vaccination_certificate_genuine.pdf",  _covid_cert,      False),
    ("covid_vaccination_certificate_forged.pdf",   _covid_cert,      True),
    ("degree_certificate_genuine.pdf",             _degree_cert,     False),
    ("degree_certificate_forged.pdf",              _degree_cert,     True),
    ("property_sale_deed_genuine.pdf",             _property_deed,   False),
    ("property_sale_deed_forged.pdf",              _property_deed,   True),
    ("fir_genuine.pdf",                            _fir,             False),
    ("fir_forged.pdf",                             _fir,             True),
]

if __name__ == "__main__":
    print(f"Generating {len(DOCS)} PDF files -> {os.path.abspath(OUT_DIR)}\n")
    for filename, fn, forged in DOCS:
        out_path = os.path.join(OUT_DIR, filename)
        fn(out_path, forged)
        tag = "FORGED  " if forged else "GENUINE "
        print(f"  [{tag}] {filename}")
    print("\nDone.")
