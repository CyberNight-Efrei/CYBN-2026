import io
import os
import secrets

import reportlab.rl_config

reportlab.rl_config.pageCompression = 0

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    FrameBreak,
    Image,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from data import STUDENTS

FLAG = os.environ.get("FLAG", "CYBN{REDACTED}")
FACES_DIR = os.path.join(os.path.dirname(__file__), "assets", "faces")

# token -> PDF bytes
_CV_STORE = {}
# student id -> token
_CV_TOKENS = {}

SIDEBAR_BG = colors.HexColor("#1f2630")
SIDEBAR_TX = colors.HexColor("#c9d4e0")
ACCENT = colors.HexColor("#4f9dff")
INK = colors.HexColor("#1b2430")
MUTED = colors.HexColor("#5c6a7a")
RULE = colors.HexColor("#e2e8f0")

PAGE_W, PAGE_H = A4
SIDEBAR_W = 6.4 * cm
MAIN_W = PAGE_W - SIDEBAR_W


def _styles():
    return {
        "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=20,
                               leading=23, textColor=colors.white),
        "role": ParagraphStyle("role", fontName="Helvetica", fontSize=10.5,
                               leading=14, textColor=ACCENT, spaceBefore=2),
        "sideHead": ParagraphStyle("sideHead", fontName="Helvetica-Bold", fontSize=10,
                                   leading=13, textColor=colors.white, spaceBefore=10,
                                   spaceAfter=4),
        "sideText": ParagraphStyle("sideText", fontName="Helvetica", fontSize=9,
                                   leading=13, textColor=SIDEBAR_TX),
        "sect": ParagraphStyle("sect", fontName="Helvetica-Bold", fontSize=12.5,
                               leading=15, textColor=INK, spaceBefore=4, spaceAfter=2),
        "sub": ParagraphStyle("sub", fontName="Helvetica-Bold", fontSize=10.5,
                              leading=14, textColor=INK, spaceBefore=6),
        "meta": ParagraphStyle("meta", fontName="Helvetica-Oblique", fontSize=9,
                               leading=12, textColor=MUTED),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5,
                               leading=13.5, textColor=INK, alignment=TA_LEFT,
                               spaceBefore=1),
        "summary": ParagraphStyle("summary", fontName="Helvetica", fontSize=9.5,
                                  leading=14, textColor=INK),
    }


def _section_title(text, st):
    bar = Table([[""]], colWidths=[1.0 * cm], rowHeights=[2.2])
    bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), ACCENT),
                             ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                             ("TOPPADDING", (0, 0), (-1, -1), 0),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return [Paragraph(text.upper(), st["sect"]), bar, Spacer(1, 4)]


def _sidebar(student, st):
    flow = []
    photo = os.path.join(FACES_DIR, f"{student['slug']}.png")
    if os.path.exists(photo):
        img = Image(photo, width=3.4 * cm, height=3.4 * cm)
        img.hAlign = "CENTER"
        flow += [img, Spacer(1, 12)]
    flow += [Paragraph(student["name"], st["name"]),
             Paragraph(student["headline"], st["role"]),
             Spacer(1, 10)]

    flow.append(Paragraph("CONTACT", st["sideHead"]))
    email = f"{student['slug']}@etu.ezea.fr"
    for line in (email, student.get("location", ""), student["promo"]):
        if line:
            flow.append(Paragraph(line, st["sideText"]))

    flow.append(Paragraph("COMPÉTENCES", st["sideHead"]))
    for tag in student["tags"]:
        flow.append(Paragraph(f"• {tag}", st["sideText"]))

    if student.get("languages"):
        flow.append(Paragraph("LANGUES", st["sideHead"]))
        for lang in student["languages"]:
            flow.append(Paragraph(lang, st["sideText"]))
    return flow


def _main(student, st):
    flow = []
    flow += _section_title("Profil", st)
    flow.append(Paragraph(student.get("summary", ""), st["summary"]))
    flow.append(Spacer(1, 10))

    flow += _section_title("Expériences", st)
    for role, org, dates, desc in student.get("experiences", []):
        flow.append(Paragraph(role, st["sub"]))
        flow.append(Paragraph(f"{org} · {dates}", st["meta"]))
        flow.append(Paragraph(desc, st["body"]))
        flow.append(Spacer(1, 4))
    flow.append(Spacer(1, 6))

    flow += _section_title("Formation", st)
    for title, dates in student.get("education", []):
        flow.append(Paragraph(title, st["sub"]))
        flow.append(Paragraph(dates, st["meta"]))
    return flow


def _draw_background(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(SIDEBAR_BG)
    canvas.rect(0, 0, SIDEBAR_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, PAGE_H - 10, SIDEBAR_W, 10, fill=1, stroke=0)
    canvas.restoreState()


def _render_cv(student):
    st = _styles()
    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0,
        title=f"CV — {student['name']}", author="ezea",
    )
    side = Frame(0, 0, SIDEBAR_W, PAGE_H,
                 leftPadding=16, rightPadding=14, topPadding=28, bottomPadding=20,
                 id="side")
    main = Frame(SIDEBAR_W, 0, MAIN_W, PAGE_H,
                 leftPadding=22, rightPadding=22, topPadding=28, bottomPadding=20,
                 id="main")
    doc.addPageTemplates([
        PageTemplate(id="cv", frames=[side, main], onPage=_draw_background)
    ])
    story = _sidebar(student, st) + [FrameBreak()] + _main(student, st)
    doc.build(story)
    return buf.getvalue()


def _resolved(student):
    s = dict(student)
    s["experiences"] = [
        (role, org, dates, desc.replace("__FLAG__", FLAG))
        for (role, org, dates, desc) in student.get("experiences", [])
    ]
    return s


def build_cvs():
    """Génère un PDF de CV par étudiant et retourne (store, tokens)."""
    _CV_STORE.clear()
    _CV_TOKENS.clear()
    for student in STUDENTS:
        token = secrets.token_urlsafe(16)
        _CV_STORE[token] = _render_cv(_resolved(student))
        _CV_TOKENS[student["id"]] = token
    return _CV_STORE, _CV_TOKENS


def cv_url_for(student_id):
    token = _CV_TOKENS.get(student_id)
    return f"/cv/{token}.pdf" if token else None


def cv_bytes(token):
    return _CV_STORE.get(token)
