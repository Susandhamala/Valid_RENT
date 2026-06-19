"""
Valid Rent — 3-page PDF certificate
  Page 1 — Details & Photos
  Page 2 — Terms & Conditions
  Page 3 — Formal Agreement / Signing Page
"""
import os
import hashlib
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage, PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

# ── Palette ────────────────────────────────────────────────────────────────────
NAVY  = colors.HexColor('#1a2e4a')
DBLUE = colors.HexColor('#1e3a5f')
BLUE  = colors.HexColor('#2563eb')
GREEN = colors.HexColor('#166534')
RED   = colors.HexColor('#991b1b')
GREY  = colors.HexColor('#475569')
LGREY = colors.HexColor('#f1f5f9')
MID   = colors.HexColor('#cbd5e1')
BLACK = colors.HexColor('#0f172a')
WHITE = colors.white
GOLD  = colors.HexColor('#92400e')

PW = A4[0]               # page width
PH = A4[1]               # page height
LM = 20 * mm             # left margin
RM = 20 * mm             # right margin
W  = PW - LM - RM        # usable width  ≈ 170 mm


# ── Style factory ──────────────────────────────────────────────────────────────
def _s(name, **kw):
    return ParagraphStyle(name, parent=getSampleStyleSheet()['Normal'], **kw)

TITLE  = _s('T',   fontSize=20, fontName='Helvetica-Bold', textColor=WHITE,
            alignment=TA_CENTER, leading=24)
SUB    = _s('Sub', fontSize=8.5, fontName='Helvetica', textColor=colors.HexColor('#93c5fd'),
            alignment=TA_CENTER, leading=12)
BODY   = _s('B',   fontSize=8.5, fontName='Helvetica',      textColor=BLACK,
            leading=13, spaceAfter=3, alignment=TA_JUSTIFY)
BODL   = _s('BL',  fontSize=8.5, fontName='Helvetica',      textColor=BLACK,
            leading=13, spaceAfter=2, alignment=TA_LEFT)
SMALL  = _s('Sm',  fontSize=7.5, fontName='Helvetica',      textColor=GREY,
            leading=11, spaceAfter=1)
MONO   = _s('M',   fontSize=6.5, fontName='Courier',        textColor=BLACK,
            leading=9,  spaceAfter=2, wordWrap='CJK')
LABEL  = _s('Lb',  fontSize=7,   fontName='Helvetica-Bold', textColor=GREY,
            leading=10, spaceAfter=1)
OK     = _s('Ok',  fontSize=8.5, fontName='Helvetica-Bold', textColor=GREEN, spaceAfter=2)
FAIL   = _s('Fl',  fontSize=8.5, fontName='Helvetica-Bold', textColor=RED,   spaceAfter=2)
LEGAL  = _s('Lg',  fontSize=9,   fontName='Helvetica',      textColor=BLACK,
            leading=15, spaceAfter=4, alignment=TA_JUSTIFY)
LEGAL_B= _s('LgB', fontSize=9,   fontName='Helvetica-Bold', textColor=BLACK,
            leading=15, spaceAfter=2)
LEGAL_H= _s('LgH', fontSize=10,  fontName='Helvetica-Bold', textColor=NAVY,
            leading=14, spaceAfter=3, spaceBefore=8)

DISCLAIMER = (
    "Valid Rent Academic Prototype · For educational use only · "
    "Not affiliated with the Government of Nepal"
)


# ── Page decorator: footer only (no distracting watermark on formal pages) ────
def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(LGREY)
    canvas.rect(0, 0, PW, 12 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(MID)
    canvas.setLineWidth(0.5)
    canvas.line(0, 12 * mm, PW, 12 * mm)
    canvas.setFont('Helvetica', 6.5)
    canvas.setFillColor(GREY)
    canvas.drawString(LM, 4.5 * mm, "Valid Rent Platform — Academic Prototype | Nepal")
    canvas.drawCentredString(PW / 2, 4.5 * mm, f"Page {doc.page} of 3")
    canvas.drawRightString(PW - RM, 4.5 * mm,
                           datetime.utcnow().strftime('%d %b %Y %H:%M UTC'))
    canvas.restoreState()


# ── Shared helpers ─────────────────────────────────────────────────────────────
def _hdr_band(title, subtitle=''):
    rows = [[Paragraph(title, TITLE)]]
    if subtitle:
        rows.append([Paragraph(subtitle, SUB)])
    t = Table(rows, colWidths=[W])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('PADDING',    (0, 0), (-1, -1), (0, 9, 0, 9)),
    ]))
    return t


def _sec(story, text):
    story.append(Spacer(1, 7))
    t = Table([[Paragraph(text, _s('sh', fontSize=8, fontName='Helvetica-Bold',
                                   textColor=WHITE))]], colWidths=[W])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DBLUE),
        ('PADDING',    (0, 0), (-1, -1), (6, 4, 6, 4)),
    ]))
    story.append(t)
    story.append(Spacer(1, 4))


def _kv_block(rows, col4=True):
    """4-col or 2-col key-value table."""
    widths = [32*mm, 53*mm, 32*mm, 53*mm] if col4 else [45*mm, W - 45*mm]
    styled = []
    for row in rows:
        sr = []
        for i, cell in enumerate(row):
            lbl = (i % 2 == 0)
            sr.append(Paragraph(str(cell) if cell not in (None, '') else '—',
                                 _s(f'kv{i}', fontSize=8,
                                    fontName='Helvetica-Bold' if lbl else 'Helvetica',
                                    textColor=GREY if lbl else BLACK)))
        styled.append(sr)
    t = Table(styled, colWidths=widths)
    t.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [LGREY, WHITE]),
        ('GRID',           (0, 0), (-1, -1), 0.3, MID),
        ('PADDING',        (0, 0), (-1, -1), 5),
        ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


def _try_img(path, w, h):
    if path and os.path.exists(path):
        try:
            img = RLImage(path, width=w, height=h)
            img.hAlign = 'CENTER'
            return img
        except Exception:
            pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def generate_certificate_pdf(
    agreement, landlord, tenant, landlord_cert, tenant_cert,
    qr_image_path, output_path, verification_code,
    landlord_photo_path=None, tenant_photo_path=None,
    tenant_document_path=None, asset_photo_path=None,
    en_legal_text: str = '', np_legal_text: str = '',   # kept for API compat, unused
):
    Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=14 * mm, bottomMargin=18 * mm,
    )

    story = []

    # ══════════════════════════════════════════════════════════════════════════
    #  PAGE 1 — DETAILS & PHOTOS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(_hdr_band(
        "VALID RENT AUTHORITY",
        "Secure Rental Certificate  ·  Details & Identity"
    ))
    story.append(Spacer(1, 6))

    # ── Certificate meta ───────────────────────────────────────────────────────
    _sec(story, "CERTIFICATE INFORMATION")
    story.append(_kv_block([
        ['Certificate No.', verification_code or 'N/A',
         'Agreement UID',   str(agreement.agreement_uid)],
        ['Status',  (agreement.status or '').upper().replace('_', ' '),
         'Generated', datetime.utcnow().strftime('%d %b %Y')],
        ['Category', agreement.rental_category or 'N/A',
         'Monthly Rent', f"{agreement.currency} {agreement.rent_amount or 0:,.0f}"],
        ['Start Date', str(agreement.start_date or '—'),
         'End Date',   str(agreement.end_date or '—')],
    ]))

    # ── Asset details + property photo side by side ────────────────────────────
    _sec(story, "RENTAL PROPERTY")
    a = agreement.asset
    asset_details_rows = []
    if a:
        asset_details_rows = [
            ['Property', a.asset_title,  'Type', a.asset_type or '—'],
            ['Location', a.location or '—', 'Ref No.', a.asset_identifier or '—'],
            ['Category', a.category.name if a.category else '—',
             'Asking Rent', f"NPR {a.estimated_value or 0:,.0f}"],
        ]
        if a.description:
            asset_details_rows.append(['Description', (a.description[:90] or '—'), '', ''])
    else:
        asset_details_rows = [['Category', agreement.rental_category or '—', '', '']]

    asset_tbl = _kv_block(asset_details_rows)
    prop_img = _try_img(asset_photo_path, 52 * mm, 40 * mm)

    if prop_img:
        lbl = Paragraph("Property Photo", LABEL)
        layout = Table(
            [[asset_tbl, [lbl, prop_img]]],
            colWidths=[W * 0.62, W * 0.38]
        )
        layout.setStyle(TableStyle([
            ('VALIGN',  (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 0),
            ('ALIGN',   (1, 0), (1, 0),   'CENTER'),
        ]))
        story.append(layout)
    else:
        story.append(asset_tbl)
    story.append(Spacer(1, 4))

    # ── Parties: photos in a 2-col grid ───────────────────────────────────────
    _sec(story, "PARTIES & IDENTITY")

    def _party_cell(user, cert, photo_path, sig_ts, cert_serial, role):
        c = []
        c.append(Paragraph(role, _s('rl', fontSize=7.5, fontName='Helvetica-Bold',
                                    textColor=WHITE, backColor=DBLUE,
                                    alignment=TA_CENTER, borderPadding=(2, 4, 2, 4),
                                    spaceAfter=4)))
        img = _try_img(photo_path, 28 * mm, 28 * mm)
        c.append(img if img else Paragraph('[No photo]', SMALL))
        c.append(Paragraph(f"<b>{user.full_name}</b>", BODL))
        c.append(Paragraph(user.email, SMALL))
        ph = getattr(user, 'phone', None) or '—'
        c.append(Paragraph(f"Ph: {ph}", SMALL))
        cs = cert.status_display if cert else 'No Certificate'
        c.append(Paragraph(f"Cert: {cs}", SMALL))
        if sig_ts:
            c.append(Paragraph("✓ SIGNED", OK))
            c.append(Paragraph(sig_ts.strftime('%d %b %Y'), SMALL))
        else:
            c.append(Paragraph("✗ NOT SIGNED", FAIL))
        return c

    half = W / 2
    parties_tbl = Table([[
        _party_cell(landlord, landlord_cert, landlord_photo_path,
                    agreement.landlord_signed_at, agreement.landlord_cert_serial, 'LANDLORD'),
        _party_cell(tenant, tenant_cert, tenant_photo_path,
                    agreement.tenant_signed_at, agreement.tenant_cert_serial, 'TENANT'),
    ]], colWidths=[half, half])
    parties_tbl.setStyle(TableStyle([
        ('ALIGN',    (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',   (0, 0), (-1, -1), 'TOP'),
        ('BOX',      (0, 0), (-1, -1), 0.5, MID),
        ('INNERGRID',(0, 0), (-1, -1), 0.5, MID),
        ('PADDING',  (0, 0), (-1, -1), 7),
    ]))
    story.append(parties_tbl)
    story.append(Spacer(1, 5))

    # ── Tenant identity document ───────────────────────────────────────────────
    doc_img = _try_img(tenant_document_path, 80 * mm, 52 * mm)
    if doc_img or (tenant_document_path and os.path.exists(tenant_document_path or '')):
        _sec(story, "TENANT IDENTITY DOCUMENT")
        if doc_img:
            it = Table([[doc_img]], colWidths=[W])
            it.setStyle(TableStyle([
                ('ALIGN',   (0, 0), (-1, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 4),
                ('BOX',     (0, 0), (-1, -1), 0.5, MID),
            ]))
            story.append(it)
        else:
            story.append(Paragraph("Identity document (PDF) submitted — on file.", BODY))
        story.append(Spacer(1, 4))

    story.append(HRFlowable(width='100%', thickness=0.5, color=MID, spaceAfter=3))
    story.append(Paragraph(DISCLAIMER,
                            _s('di', fontSize=6.5, fontName='Helvetica-Oblique',
                               textColor=GREY, alignment=TA_CENTER)))

    # ══════════════════════════════════════════════════════════════════════════
    #  PAGE 2 — TERMS & CONDITIONS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_hdr_band(
        "TERMS & CONDITIONS",
        "House Rent Act 2053  ·  Contract Act 2056  ·  Electronic Transactions Act 2063"
    ))
    story.append(Spacer(1, 8))

    TERMS = [
        ("1.  RENTAL PERIOD",
         f"This agreement runs from {agreement.start_date or 'TBD'} to "
         f"{agreement.end_date or 'TBD'}. Either party may renew by giving "
         f"30 days' written notice before expiry. Holdover without renewal does "
         f"not imply automatic extension."),

        ("2.  RENT & PAYMENT",
         f"Monthly rent is {agreement.currency} {agreement.rent_amount or 'TBD':} "
         f"payable on or before the 7th day of each month (Saptami). The Landlord "
         f"must issue a written receipt for every payment. Rent increases require "
         f"35 days' advance notice per the House Rent Act 2053."),

        ("3.  SECURITY DEPOSIT",
         "A security deposit of 1–3 months' rent must be paid before possession. "
         "It will be refunded within 15 days of vacating, less verified deductions "
         "for unpaid rent, damages beyond normal wear, or utility arrears."),

        ("4.  TENANT OBLIGATIONS",
         "The Tenant shall: (a) use the property only for its agreed lawful purpose; "
         "(b) not sub-let without the Landlord's written consent (§10, HR Act 2053); "
         "(c) maintain the property in clean, habitable condition; "
         "(d) pay all utility bills promptly; "
         "(e) not make structural alterations without written approval; "
         "(f) comply with all applicable local laws and municipal bylaws."),

        ("5.  LANDLORD OBLIGATIONS",
         "The Landlord shall: (a) hand over the property in habitable condition; "
         "(b) carry out all major structural repairs at own cost; "
         "(c) not disturb the Tenant's peaceful occupation; "
         "(d) follow due legal process before any eviction; "
         "(e) not disconnect essential utility services to coerce the Tenant."),

        ("6.  TERMINATION",
         "Either party may terminate by giving 35 days' written notice (§7, HR Act 2053). "
         "Material breach (non-payment, illegal use, unauthorised sub-letting) entitles "
         "the Landlord to apply to the Rent Hearing Committee for eviction. On termination "
         "the Tenant must vacate and return all keys within the notice period."),

        ("7.  DISPUTE RESOLUTION",
         "Disputes shall first be resolved by direct negotiation within 15 days. "
         "If unresolved, the matter goes to the Rent Hearing Committee (§14, HR Act 2053). "
         "Remaining matters are governed by the Contract Act 2056 and Civil Code 2074. "
         "Nepal courts have exclusive jurisdiction."),

        ("8.  DIGITAL SIGNATURE VALIDITY",
         "Signatures on this agreement are RSA-2048 digital signatures valid under §7 of "
         "the Electronic Transactions Act 2063. They carry the same legal force as "
         "handwritten signatures. The SHA-256 hash of this document serves as tamper "
         "evidence — any post-signing change invalidates the agreement."),
    ]

    for heading, body in TERMS:
        story.append(KeepTogether([
            Paragraph(heading, LEGAL_H),
            Paragraph(body, LEGAL),
        ]))

    # Agreed terms / remarks
    if agreement.landlord_remarks or agreement.tenant_remarks:
        story.append(Spacer(1, 6))
        _sec(story, "ADDITIONAL AGREED TERMS (RECORDED AT SIGNING)")
        if agreement.landlord_remarks:
            story.append(Paragraph("Landlord's Additional Terms:", LABEL))
            story.append(Paragraph(agreement.landlord_remarks, LEGAL))
        if agreement.tenant_remarks:
            story.append(Paragraph("Tenant's Additional Conditions:", LABEL))
            story.append(Paragraph(agreement.tenant_remarks, LEGAL))

    story.append(Spacer(1, 6))
    story.append(HRFlowable(width='100%', thickness=0.5, color=MID, spaceAfter=3))
    story.append(Paragraph(DISCLAIMER,
                            _s('di2', fontSize=6.5, fontName='Helvetica-Oblique',
                               textColor=GREY, alignment=TA_CENTER)))

    # ══════════════════════════════════════════════════════════════════════════
    #  PAGE 3 — FORMAL AGREEMENT / SIGNING PAGE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())

    # Formal top header
    story.append(Spacer(1, 4))
    story.append(Paragraph("RENTAL AGREEMENT",
                            _s('fa', fontSize=18, fontName='Helvetica-Bold',
                               textColor=NAVY, alignment=TA_CENTER)))
    story.append(Paragraph("Executed on the Valid Rent Secure Digital Platform",
                            _s('fa2', fontSize=8.5, fontName='Helvetica-Oblique',
                               textColor=GREY, alignment=TA_CENTER, spaceBefore=2,
                               spaceAfter=2)))
    story.append(HRFlowable(width='100%', thickness=2, color=NAVY, spaceAfter=10))

    # Preamble
    ll_name = landlord.full_name
    tn_name = tenant.full_name
    start   = str(agreement.start_date or '___________')
    end     = str(agreement.end_date   or '___________')
    rent    = f"{agreement.currency} {agreement.rent_amount or 0:,.0f}"
    cat     = agreement.rental_category or 'N/A'
    asset_t = a.asset_title if a else cat
    loc     = (a.location if a else None) or '___________'
    today   = datetime.utcnow().strftime('%d %B %Y')

    story.append(Paragraph(
        f'This Rental Agreement (<b>&ldquo;Agreement&rdquo;</b>) is made and entered into on '
        f'<b>{today}</b>, under the House Rent Act, 2053, the Contract Act, 2056, and the '
        f'Electronic Transactions Act, 2063 of Nepal, between the parties identified below:',
        LEGAL
    ))
    story.append(Spacer(1, 8))

    # Parties formal block
    def _formal_party(label, user, cert, cert_serial):
        rows = [
            [Paragraph(label, _s('fp', fontSize=8, fontName='Helvetica-Bold',
                                  textColor=WHITE))],
            [_kv_block([
                ['Full Name',  user.full_name,  'Email',   user.email],
                ['Phone',      getattr(user, 'phone', None) or '—',
                 'Certificate', cert.status_display if cert else 'Not Issued'],
                ['Cert Serial', cert_serial or '—', '', ''],
            ], col4=True)],
        ]
        outer = Table(rows, colWidths=[W])
        outer.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), DBLUE),
            ('PADDING',    (0, 0), (0, 0), (6, 4, 6, 4)),
            ('PADDING',    (0, 1), (0, 1), 0),
            ('BOX',        (0, 0), (-1, -1), 0.8, NAVY),
        ]))
        return outer

    story.append(_formal_party(
        "PARTY A — LANDLORD (Owner / Lessor)",
        landlord, landlord_cert, agreement.landlord_cert_serial
    ))
    story.append(Spacer(1, 6))
    story.append(_formal_party(
        "PARTY B — TENANT (Occupant / Lessee)",
        tenant, tenant_cert, agreement.tenant_cert_serial
    ))
    story.append(Spacer(1, 8))

    # Property summary
    prop_rows = [
        [Paragraph("SUBJECT PROPERTY", _s('sph', fontSize=8, fontName='Helvetica-Bold',
                                           textColor=WHITE))],
        [_kv_block([
            ['Property',  asset_t,  'Location', loc],
            ['Period',    f"{start} → {end}", 'Monthly Rent', rent],
        ], col4=True)],
    ]
    prop_outer = Table(prop_rows, colWidths=[W])
    prop_outer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), DBLUE),
        ('PADDING',    (0, 0), (0, 0), (6, 4, 6, 4)),
        ('PADDING',    (0, 1), (0, 1), 0),
        ('BOX',        (0, 0), (-1, -1), 0.8, NAVY),
    ]))
    story.append(prop_outer)
    story.append(Spacer(1, 10))

    # Agreement body
    story.append(Paragraph(
        f"Both parties confirm that they have read, understood, and accepted all terms "
        f"and conditions set forth in this Agreement and the attached Terms & Conditions "
        f"(Page 2). The Landlord and Tenant hereby agree that the property described above "
        f"shall be leased from <b>{start}</b> to <b>{end}</b> at a monthly rent of "
        f"<b>{rent}</b>, subject to all conditions stated herein.",
        LEGAL
    ))
    story.append(Paragraph(
        "By affixing their RSA-2048 digital signatures below, both parties declare that:",
        LEGAL
    ))
    declarations = [
        "(i)   They have freely and voluntarily entered into this Agreement without coercion;",
        "(ii)  Their digital signature constitutes a legally binding electronic signature "
        "under §7 of the Electronic Transactions Act, 2063;",
        "(iii) This Agreement is enforceable in Nepal courts with the same force as a "
        "physically signed document under the Civil Code, 2074;",
        "(iv)  The SHA-256 hash below serves as tamper-evidence — any post-signing "
        "alteration voids this Agreement.",
    ]
    for d in declarations:
        story.append(Paragraph(d, _s('dc', fontSize=8.5, fontName='Helvetica',
                                     textColor=BLACK, leading=14, spaceAfter=3,
                                     leftIndent=10)))
    story.append(Spacer(1, 8))

    # Signature blocks
    story.append(Paragraph("EXECUTED AND AGREED BY BOTH PARTIES",
                            _s('exh', fontSize=9, fontName='Helvetica-Bold',
                               textColor=NAVY, alignment=TA_CENTER, spaceAfter=6)))

    def _sig_block(user, cert, photo_path, sig_ts, cert_serial, signature, role):
        lines = []
        img = _try_img(photo_path, 22 * mm, 22 * mm)
        lines.append(Paragraph(role, _s('sr', fontSize=8, fontName='Helvetica-Bold',
                                        textColor=WHITE, alignment=TA_CENTER,
                                        backColor=NAVY, borderPadding=(2, 4, 2, 4),
                                        spaceAfter=4)))
        if img:
            lines.append(img)
        lines.append(Paragraph(f"<b>{user.full_name}</b>", BODL))
        lines.append(Paragraph(user.email, SMALL))
        lines.append(Spacer(1, 4))
        if sig_ts:
            lines.append(Paragraph("DIGITALLY SIGNED", OK))
            lines.append(Paragraph(f"Date: {sig_ts.strftime('%d %B %Y, %H:%M UTC')}", SMALL))
            if cert_serial:
                lines.append(Paragraph(f"Certificate: {cert_serial}", SMALL))
            if signature:
                lines.append(Paragraph("RSA-2048 Signature (truncated):", LABEL))
                lines.append(Paragraph(signature[:80] + '…', MONO))
        else:
            lines.append(Paragraph("NOT YET SIGNED", FAIL))
        return lines

    l_ok = agreement.landlord_signature is not None
    t_ok = agreement.tenant_signature is not None

    sig_tbl = Table([[
        _sig_block(landlord, landlord_cert, landlord_photo_path,
                   agreement.landlord_signed_at, agreement.landlord_cert_serial,
                   agreement.landlord_signature, 'LANDLORD'),
        _sig_block(tenant, tenant_cert, tenant_photo_path,
                   agreement.tenant_signed_at, agreement.tenant_cert_serial,
                   agreement.tenant_signature, 'TENANT'),
    ]], colWidths=[W / 2, W / 2])
    sig_tbl.setStyle(TableStyle([
        ('ALIGN',    (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',   (0, 0), (-1, -1), 'TOP'),
        ('BOX',      (0, 0), (-1, -1), 1, NAVY),
        ('INNERGRID',(0, 0), (-1, -1), 0.5, MID),
        ('PADDING',  (0, 0), (-1, -1), 8),
    ]))
    story.append(sig_tbl)
    story.append(Spacer(1, 8))

    # Verification row: hash + QR
    ver_label = ("✓  AGREEMENT FULLY EXECUTED — BOTH PARTIES SIGNED"
                 if (l_ok and t_ok)
                 else "⏳  PENDING — ONE OR BOTH SIGNATURES OUTSTANDING")
    story.append(Paragraph(ver_label, OK if (l_ok and t_ok) else FAIL))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Cryptographic Document Hash (SHA-256):", LABEL))
    story.append(Paragraph(agreement.document_hash_sha256 or '—', MONO))
    story.append(Spacer(1, 4))

    # QR + verify note
    qr_img = _try_img(qr_image_path, 30 * mm, 30 * mm)
    if qr_img:
        qr_row = Table([[
            qr_img,
            [Paragraph("Scan to verify this certificate online:", SMALL),
             Paragraph(f"Code: {verification_code}", MONO),
             Paragraph(f"URL: /verify/code/{verification_code}", MONO)],
        ]], colWidths=[35 * mm, W - 35 * mm])
        qr_row.setStyle(TableStyle([
            ('VALIGN',  (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('BOX',     (0, 0), (-1, -1), 0.5, MID),
        ]))
        story.append(qr_row)
        story.append(Spacer(1, 6))

    story.append(HRFlowable(width='100%', thickness=1, color=NAVY, spaceAfter=4))
    story.append(Paragraph(
        "THIS RENTAL AGREEMENT IS LEGALLY BINDING UNDER NEPALI LAW FROM THE DATE "
        "OF BOTH PARTIES' DIGITAL SIGNATURES.",
        _s('final', fontSize=8, fontName='Helvetica-Bold',
           textColor=NAVY, alignment=TA_CENTER, spaceAfter=2)
    ))
    story.append(Paragraph(DISCLAIMER,
                            _s('di3', fontSize=6.5, fontName='Helvetica-Oblique',
                               textColor=GREY, alignment=TA_CENTER)))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return hashlib.sha256(open(output_path, 'rb').read()).hexdigest()
