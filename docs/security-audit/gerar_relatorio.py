# -*- coding: utf-8 -*-
"""Gerador do relatório PDF de auditoria de segurança.

Dependências (ambiente isolado, nunca global):
    python -m venv .venv
    .venv\\Scripts\\pip install reportlab matplotlib pymupdf

Uso:
    .venv\\Scripts\\python docs/security-audit/gerar_relatorio.py

Saídas:
    docs/security-audit/relatorio-auditoria-seguranca.pdf
    docs/security-audit/graficos/severidade.png
    docs/security-audit/graficos/categorias.png
"""

from __future__ import annotations

import os
import textwrap
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Flowable,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    LongTable,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

from dados_auditoria import (
    CATEGORIES,
    FINDINGS,
    RECOMMENDATIONS,
    ROUTES,
    STRENGTHS,
    TRECHOS,
    WEAKNESSES,
)
from issues_github import ISSUES

# ---------------------------------------------------------------------------
# Caminhos e paleta
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
PDF_PATH = BASE_DIR / "relatorio-auditoria-seguranca.pdf"
CHART_DIR = BASE_DIR / "graficos"

NAVY = HexColor("#0F172A")
NAVY_2 = HexColor("#1E293B")
SLATE = HexColor("#334155")
MUTED = HexColor("#64748B")
TEXT = HexColor("#1E293B")
BORDER = HexColor("#E2E8F0")
LIGHT = HexColor("#F8FAFC")
WHITE = colors.white
EMERALD = HexColor("#059669")
EMERALD_LIGHT = HexColor("#ECFDF5")
AMBER_LIGHT = HexColor("#FFFBEB")
RED_LIGHT = HexColor("#FEF2F2")
BLUE_LIGHT = HexColor("#EFF6FF")

SEVERITY_COLORS = {
    "Crítica": HexColor("#B91C1C"),
    "Alta": HexColor("#EA580C"),
    "Média": HexColor("#D97706"),
    "Baixa": HexColor("#2563EB"),
    "Informativa": HexColor("#64748B"),
}
SEVERITY_ORDER = ["Crítica", "Alta", "Média", "Baixa", "Informativa"]
SEVERITY_HEX = {
    "Crítica": "#B91C1C",
    "Alta": "#EA580C",
    "Média": "#D97706",
    "Baixa": "#2563EB",
    "Informativa": "#64748B",
}
STATUS_COLORS = {
    "OK": EMERALD,
    "IDOR": SEVERITY_COLORS["Crítica"],
    "Risco latente": SEVERITY_COLORS["Média"],
    "Baixo": SEVERITY_COLORS["Baixa"],
    "Exposição": SEVERITY_COLORS["Alta"],
    "Falha de integridade": SEVERITY_COLORS["Alta"],
}

TODAY = datetime.now()
DATE_SHORT = TODAY.strftime("%d/%m/%Y")
DATE_LONG = f"{TODAY.day} de {['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'][TODAY.month - 1]} de {TODAY.year}"
MONTH_YEAR = f"{['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][TODAY.month - 1]}/{TODAY.year}"

# ---------------------------------------------------------------------------
# Fontes e estilos
# ---------------------------------------------------------------------------

FONT = "Helvetica"
FONT_B = "Helvetica-Bold"
FONT_I = "Helvetica-Oblique"
FONT_BI = "Helvetica-BoldOblique"
MONO = "Courier"
MONO_B = "Courier-Bold"


def _first_existing(paths: Iterable[str]) -> str | None:
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def registrar_fontes() -> None:
    """Registra Segoe UI/Consolas quando disponíveis; senão usa as built-ins."""
    global FONT, FONT_B, FONT_I, FONT_BI, MONO, MONO_B
    win = Path(r"C:\Windows\Fonts")
    regular = _first_existing(
        [str(win / "segoeui.ttf"), str(win / "arial.ttf"), "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    bold = _first_existing(
        [str(win / "segoeuib.ttf"), str(win / "arialbd.ttf"), "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    )
    italic = _first_existing(
        [str(win / "segoeuii.ttf"), str(win / "ariali.ttf"), "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"]
    )
    bold_italic = _first_existing(
        [str(win / "segoeuiz.ttf"), str(win / "arialbi.ttf"), "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"]
    )
    mono = _first_existing(
        [str(win / "consola.ttf"), str(win / "cour.ttf"), "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
    )
    mono_b = _first_existing(
        [str(win / "consolab.ttf"), str(win / "courbd.ttf"), "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"]
    )
    if regular and bold:
        pdfmetrics.registerFont(TTFont("Corpo", regular))
        pdfmetrics.registerFont(TTFont("Corpo-Bold", bold))
        pdfmetrics.registerFont(TTFont("Corpo-Italic", italic or regular))
        pdfmetrics.registerFont(TTFont("Corpo-BoldItalic", bold_italic or bold))
        pdfmetrics.registerFontFamily(
            "Corpo",
            normal="Corpo",
            bold="Corpo-Bold",
            italic="Corpo-Italic",
            boldItalic="Corpo-BoldItalic",
        )
        FONT, FONT_B, FONT_I, FONT_BI = "Corpo", "Corpo-Bold", "Corpo-Italic", "Corpo-BoldItalic"
    if mono:
        pdfmetrics.registerFont(TTFont("Mono", mono))
        pdfmetrics.registerFont(TTFont("Mono-Bold", mono_b or mono))
        pdfmetrics.registerFontFamily("Mono", normal="Mono", bold="Mono-Bold", italic="Mono", boldItalic="Mono-Bold")
        MONO, MONO_B = "Mono", "Mono-Bold"


registrar_fontes()


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "body": ParagraphStyle(
            "body",
            fontName=FONT,
            fontSize=9.2,
            leading=13.6,
            textColor=TEXT,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "body_left": ParagraphStyle(
            "body_left",
            fontName=FONT,
            fontSize=9.2,
            leading=13.4,
            textColor=TEXT,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "lead": ParagraphStyle(
            "lead",
            fontName=FONT,
            fontSize=10.4,
            leading=15.4,
            textColor=SLATE,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "h1": ParagraphStyle(
            "h1",
            fontName=FONT_B,
            fontSize=17,
            leading=21,
            textColor=NAVY,
            spaceBefore=2,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName=FONT_B,
            fontSize=12.2,
            leading=15.5,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "h3",
            fontName=FONT_B,
            fontSize=10.2,
            leading=13,
            textColor=SLATE,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "kicker": ParagraphStyle(
            "kicker",
            fontName=FONT_B,
            fontSize=9,
            leading=12,
            textColor=EMERALD,
            spaceAfter=8,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            fontName=FONT_B,
            fontSize=27,
            leading=33,
            textColor=WHITE,
            spaceAfter=4,
        ),
        "cover_project": ParagraphStyle(
            "cover_project",
            fontName=FONT_B,
            fontSize=34,
            leading=40,
            textColor=EMERALD,
            spaceAfter=12,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            fontName=FONT,
            fontSize=10.5,
            leading=15,
            textColor=HexColor("#CBD5E1"),
            spaceAfter=4,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            fontName=FONT,
            fontSize=7.4,
            leading=10.4,
            textColor=HexColor("#CBD5E1"),
        ),
        "cover_note": ParagraphStyle(
            "cover_note",
            fontName=FONT,
            fontSize=7.4,
            leading=10.5,
            textColor=HexColor("#94A3B8"),
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName=FONT_I,
            fontSize=7.8,
            leading=10,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "small": ParagraphStyle(
            "small",
            fontName=FONT,
            fontSize=8,
            leading=11.2,
            textColor=MUTED,
            spaceAfter=4,
        ),
        "table_head": ParagraphStyle(
            "table_head",
            fontName=FONT_B,
            fontSize=7.2,
            leading=9.2,
            textColor=WHITE,
            alignment=TA_LEFT,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            fontName=FONT,
            fontSize=7.6,
            leading=10.2,
            textColor=TEXT,
            alignment=TA_LEFT,
        ),
        "table_cell_tight": ParagraphStyle(
            "table_cell_tight",
            fontName=FONT,
            fontSize=7.1,
            leading=9.4,
            textColor=TEXT,
            alignment=TA_LEFT,
        ),
        "mono_cell": ParagraphStyle(
            "mono_cell",
            fontName=MONO,
            fontSize=6.7,
            leading=8.6,
            textColor=SLATE,
            alignment=TA_LEFT,
        ),
        "card_title": ParagraphStyle(
            "card_title",
            fontName=FONT_B,
            fontSize=9.4,
            leading=12,
            textColor=NAVY,
            spaceAfter=2,
        ),
        "card_text": ParagraphStyle(
            "card_text",
            fontName=FONT,
            fontSize=8.4,
            leading=11.6,
            textColor=SLATE,
            alignment=TA_LEFT,
            spaceAfter=3,
        ),
        "card_evidence": ParagraphStyle(
            "card_evidence",
            fontName=MONO,
            fontSize=6.9,
            leading=9,
            textColor=SLATE,
            spaceAfter=3,
        ),
        "kpi_num": ParagraphStyle(
            "kpi_num",
            fontName=FONT_B,
            fontSize=21,
            leading=23,
            textColor=WHITE,
            alignment=TA_CENTER,
            spaceAfter=1,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label",
            fontName=FONT_B,
            fontSize=6.8,
            leading=8.4,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),
        "code": ParagraphStyle(
            "code",
            fontName=MONO,
            fontSize=6.2,
            leading=8.4,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=0,
        ),
        "callout": ParagraphStyle(
            "callout",
            fontName=FONT,
            fontSize=8.4,
            leading=11.8,
            textColor=HexColor("#78350F"),
            alignment=TA_LEFT,
        ),
        "callout_title": ParagraphStyle(
            "callout_title",
            fontName=FONT_B,
            fontSize=8.8,
            leading=11.4,
            textColor=HexColor("#92400E"),
            spaceAfter=2,
        ),
        "issue": ParagraphStyle(
            "issue",
            fontName=MONO,
            fontSize=6.35,
            leading=8.05,
            textColor=TEXT,
            alignment=TA_LEFT,
            spaceAfter=0,
        ),
        "delim": ParagraphStyle(
            "delim",
            fontName=MONO_B,
            fontSize=7.2,
            leading=9.6,
            textColor=NAVY,
            alignment=TA_LEFT,
        ),
        "issue_title": ParagraphStyle(
            "issue_title",
            fontName=FONT_B,
            fontSize=8.6,
            leading=11.2,
            textColor=WHITE,
        ),
    }


S = _styles()

# ---------------------------------------------------------------------------
# Helpers de conteúdo
# ---------------------------------------------------------------------------


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def mono(text: str, size: float = 6.8) -> str:
    return f'<font name="{MONO}" size="{size}">{esc(text)}</font>'


def mono_wrap_files(text: str, size: float = 6.0, limit: int = 36) -> str:
    """Mono com uma linha por arquivo e quebra em vírgulas quando necessário."""
    groups = text.split("; ")
    lines: list[str] = []
    for gi, group in enumerate(groups):
        suffix = ";" if gi < len(groups) - 1 else ""
        if len(group) <= limit:
            lines.append(group + suffix)
            continue
        parts = group.split(",")
        line = parts[0]
        for part in parts[1:]:
            if len(line) + 1 + len(part) <= limit:
                line = f"{line},{part}"
            else:
                lines.append(line + ",")
                line = part
        lines.append(line + suffix)
    return "<br/>".join(f'<font name="{MONO}" size="{size}">{esc(line)}</font>' for line in lines)


def p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, S[style])


def count_by_severity() -> Counter:
    return Counter(f.severity for f in FINDINGS)


def count_by_category() -> Counter:
    return Counter(f.category for f in FINDINGS)


def severity_summary() -> str:
    c = count_by_severity()

    def qtd(n: int, singular: str, plural: str) -> str:
        return f"{n} {singular if n == 1 else plural}"

    return (
        f"{len(FINDINGS)} achados: {qtd(c['Crítica'], 'crítica', 'críticas')}, "
        f"{qtd(c['Alta'], 'alta', 'altas')}, {qtd(c['Média'], 'média', 'médias')}, "
        f"{qtd(c['Baixa'], 'baixa', 'baixas')} e {qtd(c['Informativa'], 'informativa', 'informativas')}."
    )


# ---------------------------------------------------------------------------
# Componentes visuais
# ---------------------------------------------------------------------------


class Chip(Flowable):
    """Chip arredondado de severidade."""

    def __init__(self, label: str, bg, fg=WHITE, width: float = 1.92 * cm, height: float = 0.52 * cm):
        super().__init__()
        self.label = label
        self.bg = bg
        self.fg = fg
        self.width = width
        self.height = height

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.roundRect(0, 0, self.width, self.height, 3.2, stroke=0, fill=1)
        c.setFillColor(self.fg)
        c.setFont(FONT_B, 6.4)
        c.drawCentredString(self.width / 2, self.height / 2 - 2.2, self.label.upper())


class NumberedCanvas(canvas.Canvas):
    """Canvas que sabe o total de páginas para o rodapé 'Página X de Y'."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if self._pageNumber > 1:
                self.setFont(FONT, 7.2)
                self.setFillColor(MUTED)
                self.drawRightString(A4[0] - 2 * cm, 0.95 * cm, f"Página {self._pageNumber} de {total}")
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


def draw_cover(c: canvas.Canvas, doc) -> None:
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)

    # Formas decorativas discretas
    c.setFillColor(NAVY_2)
    c.circle(A4[0] - 1.6 * cm, A4[1] - 2.0 * cm, 5.4 * cm, stroke=0, fill=1)
    c.setFillColor(SLATE)
    c.circle(A4[0] - 5.4 * cm, A4[1] - 6.8 * cm, 2.3 * cm, stroke=0, fill=1)
    c.setFillColor(EMERALD)
    c.rect(2 * cm, A4[1] - 1.75 * cm, 2.4 * cm, 0.12 * cm, stroke=0, fill=1)

    c.setFillColor(EMERALD)
    c.setFont(FONT_B, 8)
    c.drawString(2 * cm, A4[1] - 1.55 * cm, "GABARITEI")
    c.setFillColor(HexColor("#94A3B8"))
    c.setFont(FONT, 7.4)
    c.drawRightString(A4[0] - 2 * cm, A4[1] - 1.55 * cm, "AUDITORIA 2026")

    c.setStrokeColor(HexColor("#334155"))
    c.setLineWidth(0.6)
    c.line(2 * cm, 2.55 * cm, A4[0] - 2 * cm, 2.55 * cm)
    c.setFillColor(HexColor("#94A3B8"))
    c.setFont(FONT, 6.8)
    c.drawString(
        2 * cm,
        2.05 * cm,
        "Documento gerado por análise estática de código. Nenhuma consulta foi executada contra a produção.",
    )
    c.drawRightString(A4[0] - 2 * cm, 2.05 * cm, "v1.0")
    c.restoreState()


def draw_body(c: canvas.Canvas, doc) -> None:
    c.saveState()
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(2 * cm, A4[1] - 1.55 * cm, A4[0] - 2 * cm, A4[1] - 1.55 * cm)
    c.setFillColor(MUTED)
    c.setFont(FONT, 7.2)
    c.drawString(2 * cm, A4[1] - 1.38 * cm, "Relatório de Auditoria de Segurança — Gabaritei Questões")
    c.drawRightString(A4[0] - 2 * cm, A4[1] - 1.38 * cm, MONTH_YEAR)
    c.setStrokeColor(BORDER)
    c.line(2 * cm, 1.45 * cm, A4[0] - 2 * cm, 1.45 * cm)
    c.setFillColor(MUTED)
    c.setFont(FONT, 7.2)
    c.drawString(2 * cm, 0.95 * cm, "gabaritei-questoes • Auditoria de Segurança")
    c.restoreState()


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------


def gerar_graficos() -> tuple[Path, Path]:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = "DejaVu Sans"
    counts = count_by_severity()
    total = sum(counts.values())

    # Donut por severidade
    fig, ax = plt.subplots(figsize=(8.4, 3.35), dpi=220)
    values = [counts[s] for s in SEVERITY_ORDER]
    labels = [f"{s} — {counts[s]} ({counts[s] / total * 100:.0f}%)" for s in SEVERITY_ORDER]
    wedges, _ = ax.pie(
        values,
        colors=[SEVERITY_HEX[s] for s in SEVERITY_ORDER],
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.38, edgecolor="white", linewidth=2.2),
    )
    ax.text(0, 0.10, str(total), ha="center", va="center", fontsize=24, fontweight="bold", color="#0F172A")
    ax.text(0, -0.18, "achados", ha="center", va="center", fontsize=8.4, color="#64748B")
    ax.legend(
        wedges,
        labels,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=8.2,
        handlelength=1.1,
        labelspacing=0.8,
    )
    ax.set_aspect("equal")
    plt.tight_layout()
    donut = CHART_DIR / "severidade.png"
    fig.savefig(donut, bbox_inches="tight", pad_inches=0.08, facecolor="white")
    plt.close(fig)

    # Barras empilhadas por categoria
    cat_codes = [c.code for c in CATEGORIES]
    short_names = {
        "1": "Cat. 1\nIsolamento",
        "2": "Cat. 2\nPermissão",
        "3": "Cat. 3\nIDOR",
        "4": "Cat. 4\nChaves",
        "5": "Cat. 5\nXSS",
    }
    fig, ax = plt.subplots(figsize=(8.4, 3.7), dpi=220)
    x = list(range(len(cat_codes)))
    bottom = [0] * len(cat_codes)
    for sev in SEVERITY_ORDER:
        vals = [sum(1 for f in FINDINGS if f.category == code and f.severity == sev) for code in cat_codes]
        ax.bar(
            x,
            vals,
            bottom=bottom,
            color=SEVERITY_HEX[sev],
            label=sev,
            width=0.55,
            edgecolor="white",
            linewidth=0.7,
        )
        bottom = [b + v for b, v in zip(bottom, vals)]
    for i, total_cat in enumerate(bottom):
        ax.text(i, total_cat + 0.12, str(total_cat), ha="center", va="bottom", fontsize=8.6, fontweight="bold", color="#1E293B")
    ax.set_xticks(x)
    ax.set_xticklabels([short_names[c] for c in cat_codes], fontsize=7.8, color="#475569")
    ax.set_ylabel("Achados", fontsize=8, color="#475569")
    ax.set_ylim(0, max(bottom) + 1.3)
    ax.tick_params(axis="y", labelsize=7.6, colors="#64748B")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#E2E8F0")
    ax.spines["bottom"].set_color("#E2E8F0")
    ax.grid(axis="y", color="#E2E8F0", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(
        [Patch(facecolor=SEVERITY_HEX[s], label=s) for s in SEVERITY_ORDER],
        SEVERITY_ORDER,
        ncol=5,
        fontsize=7.4,
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.14),
        handlelength=1.0,
        columnspacing=1.4,
    )
    plt.tight_layout()
    bars = CHART_DIR / "categorias.png"
    fig.savefig(bars, bbox_inches="tight", pad_inches=0.08, facecolor="white")
    plt.close(fig)
    return donut, bars


# ---------------------------------------------------------------------------
# Seções iniciais
# ---------------------------------------------------------------------------


def build_cover() -> list:
    story: list = [NextPageTemplate("Body")]
    story.append(Spacer(1, 2.4 * cm))
    story.append(p("AUDITORIA DE SEGURANÇA", "kicker"))
    story.append(p("Relatório de Auditoria<br/>de Segurança", "cover_title"))
    story.append(p("Gabaritei Questões", "cover_project"))
    story.append(
        p(
            "Revisão de isolamento de dados, autorização, IDOR, segredos e XSS "
            "em uma aplicação Flask + Supabase + Electron.",
            "cover_sub",
        )
    )
    story.append(Spacer(1, 0.35 * cm))
    story.append(Chip("1 ACHADO CRÍTICO", SEVERITY_COLORS["Crítica"], width=4.2 * cm, height=0.66 * cm))
    story.append(Spacer(1, 0.55 * cm))
    story.append(HRFlowable(width="100%", thickness=1.6, color=EMERALD, spaceBefore=0, spaceAfter=12))

    meta = [
        [
            p(f"<font size='7' color='#94A3B8'>DATA</font><br/><font size='10' color='white'><b>{DATE_SHORT}</b></font>", "cover_meta"),
            p("<font size='7' color='#94A3B8'>ESCOPO</font><br/><font size='9' color='white'>11 blueprints, 80+ handlers, templates/JS, docs, .env, git e bundle Electron</font>", "cover_meta"),
        ],
        [
            p("<font size='7' color='#94A3B8'>STACK</font><br/><font size='9' color='white'>Python/Flask, Supabase/PostgREST, Jinja2, Tailwind/Bootstrap, Electron</font>", "cover_meta"),
            p("<font size='7' color='#94A3B8'>RESULTADO</font><br/><font size='9' color='white'>15 achados • 9 issues para o GitHub</font>", "cover_meta"),
        ],
    ]
    meta_table = Table(meta, colWidths=[8.25 * cm, 8.25 * cm], rowHeights=[2.15 * cm, 2.15 * cm])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY_2),
                ("BOX", (0, 0), (-1, -1), 0.6, HexColor("#334155")),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, HexColor("#334155")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 0.55 * cm))
    story.append(
        p(
            "Nota metodológica: cada categoria foi mapeada para o equivalente da stack detectada. "
            "A seção 3 detalha o escopo, as limitações e a cobertura rota a rota.",
            "cover_note",
        )
    )
    story.append(PageBreak())
    return story


def build_summary() -> list:
    c = count_by_severity()
    story: list = [p("1. Resumo executivo", "h1")]
    story.append(
        p(
            f"A auditoria estática identificou <b>{severity_summary()}</b> O risco central não é "
            "um endpoint isolado: é a combinação de uma policy de SELECT documentada como livre "
            "com uma anon key pública, que transforma a leitura de dados de aluno em um dump "
            "cross-tenant sem autenticação. Sobre essa base, foram confirmados IDORs em cadernos "
            "e simulados privados, um XSS armazenado em comentários e uma rota legada que confia "
            "no placar enviado pelo cliente.",
            "lead",
        )
    )

    kpis = [
        ("TOTAL", len(FINDINGS), NAVY),
        ("CRÍTICA", c["Crítica"], SEVERITY_COLORS["Crítica"]),
        ("ALTA", c["Alta"], SEVERITY_COLORS["Alta"]),
        ("MÉDIA", c["Média"], SEVERITY_COLORS["Média"]),
        ("BAIXA", c["Baixa"], SEVERITY_COLORS["Baixa"]),
        ("INFO", c["Informativa"], SEVERITY_COLORS["Informativa"]),
    ]
    kpi_cells = []
    for label, value, color in kpis:
        kpi_cells.append([p(str(value), "kpi_num"), p(label, "kpi_label")])
    kpi_table = Table([kpi_cells], colWidths=[17 * cm / 6] * 6, rowHeights=[1.72 * cm])
    kpi_style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, (_, _, color) in enumerate(kpis):
        kpi_style.append(("BACKGROUND", (i, 0), (i, 0), color))
    kpi_table.setStyle(TableStyle(kpi_style))
    story.append(kpi_table)
    story.append(Spacer(1, 0.35 * cm))

    story.append(p("Leitura rápida", "h3"))
    bullets = [
        "<b>O SELECT é a porteira aberta.</b> A documentação afirma que 13 tabelas de dados do "
        "aluno têm SELECT livre para anon; a anon key está no cliente. Sem login, é possível ler "
        "e-mails, histórico, comentários, cadernos, flashcards e simulados de todos.",
        "<b>Os IDORs sobrevivem ao RLS.</b> Mesmo que o SELECT seja fechado, cadernos e simulados "
        "privados continuam acessíveis por ID porque as rotas não comparam o dono.",
        "<b>O XSS é armazenado e cross-user.</b> Texto e nome de usuário entram crus no innerHTML; "
        "o CSP com unsafe-inline permite o handler. O payload atinge qualquer leitor da questão.",
        "<b>O restante do backend tem boa disciplina.</b> CSRF global, aluno_required no servidor, "
        "filtros de dono na maior parte do CRUD e correção server-side na rota principal de resposta.",
    ]
    for b in bullets:
        story.append(p(f"• {b}", "body_left"))

    story.append(Spacer(1, 0.25 * cm))
    callout = Table(
        [
            [
                p(
                    "<b>Condições de explorabilidade</b><br/>"
                    "A falha crítica é documental: as migrations de RLS não estão no repositório. "
                    "Não foi executada consulta contra a produção; a exploração depende de a "
                    "configuração descrita em docs/banco_dados.md estar vigente. Os IDORs exigem "
                    "um aluno autenticado e IDs numéricos. O XSS exige que a vítima abra/expanda "
                    "os comentários da questão. A rota /api/responder não é chamada pelo frontend "
                    "atual, mas permanece acessível.",
                    "callout",
                )
            ]
        ],
        colWidths=[17 * cm],
    )
    callout.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), AMBER_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.8, HexColor("#FCD34D")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(callout)
    story.append(PageBreak())
    return story


def build_charts(donut: Path, bars: Path) -> list:
    story: list = [p("2. Visão quantitativa", "h1")]
    story.append(
        p(
            "Os gráficos abaixo usam a paleta definida para o relatório. A distribuição por "
            "severidade mostra o peso da falha crítica de RLS; a distribuição por categoria "
            "mostra que o IDOR é o grupo mais numeroso, seguido por isolamento e chaves.",
            "body",
        )
    )
    story.append(Image(str(donut), width=16.4 * cm, height=6.54 * cm))
    story.append(p("Figura 1 — Achados por severidade (total e percentual).", "caption"))
    story.append(Image(str(bars), width=16.4 * cm, height=7.22 * cm))
    story.append(p("Figura 2 — Achados por categoria, empilhados por severidade.", "caption"))
    story.append(
        p(
            "<b>Como ler:</b> a categoria 3 (IDOR) concentra 7 dos 15 achados, mas a categoria 1 "
            "contém o único achado crítico e o de maior impacto sistêmico. A categoria 4 é "
            "majoritariamente informativa: a anon key é pública por design e o APP_TOKEN é "
            "extraível, mas nenhum dos dois, sozinho, permite escrever como outro aluno. A "
            "categoria 5 tem um XSS alto e um conjunto de sinks latentes.",
            "body",
        )
    )
    story.append(PageBreak())
    return story


def build_methodology() -> list:
    story: list = [p("3. Escopo e metodologia", "h1")]
    story.append(
        p(
            "A stack foi detectada antes da auditoria e cada categoria foi adaptada ao equivalente "
            "dela. Foram lidos todos os módulos de rota, os módulos de banco/utilitários, os "
            "templates e o JavaScript, a documentação de segurança e de rotas, o .env, o histórico "
            "git, o site público e o bundle Electron. Não foram executados exploits contra a "
            "produção nem consultas a dados reais de alunos.",
            "body",
        )
    )

    stack_rows = [
        ("Linguagem / framework", "Python 3 + Flask; Flask-Login, Flask-WTF (CSRF), Flask-Limiter, Flask-Talisman."),
        ("Banco / query builder", "Supabase PostgreSQL via PostgREST (SDK supabase/postgrest), ANON key + header x-app-token."),
        ("Frontend", "Jinja2 + Tailwind/Bootstrap + JavaScript vanilla; marked.js, KaTeX, SweetAlert2."),
        ("Desktop", "Electron (contextIsolation, sandbox, nodeIntegration false) + backend PyInstaller."),
        ("Deploy", "Sem Docker/CI/Helm/Terraform no repositório; backend escuta 127.0.0.1:5000."),
    ]
    stack_table = Table(
        [[p(f"<b>{k}</b>", "table_cell"), p(v, "table_cell")] for k, v in stack_rows],
        colWidths=[4.1 * cm, 12.9 * cm],
    )
    stack_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(stack_table)
    story.append(Spacer(1, 0.35 * cm))

    story.append(p("3.1 Mapeamento das cinco categorias", "h2"))
    header = [
        p("Categoria", "table_head"),
        p("Equivalente na stack", "table_head"),
        p("Como foi verificado", "table_head"),
    ]
    verification = {
        "1": "Leitura das policies documentadas, de todas as queries e dos filtros por id_usuario; confronto com o modelo de dados.",
        "2": "Inventário de gates de papel no frontend e no backend; confirmação de que não há UI/admin neste repo; revisão de lógica de negócio confiada ao cliente.",
        "3": "Leitura de todos os handlers das 11 blueprints; tabela de cobertura com cada rota que recebe ID ou muta dados.",
        "4": "Busca por chaves/tokens/senhas em código, configs, docs e bundle; git log/git grep; inspeção do app.asar; .env e .env.example.",
        "5": "Varredura de innerHTML, |safe, marked.parse, srcdoc e eval; verificação de sanitizador nas dependências; análise do CSP.",
    }
    rows = [header]
    for cat in CATEGORIES:
        rows.append([p(f"<b>{cat.code}. {cat.name}</b>", "table_cell"), p(cat.mapping, "table_cell"), p(verification[cat.code], "table_cell")])
    method_table = LongTable(rows, colWidths=[3.6 * cm, 6.2 * cm, 7.2 * cm], repeatRows=1)
    method_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(method_table)
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        p(
            "<b>Categoria 2 — não se aplica à UI administrativa.</b> Este repositório não contém "
            "tela, rota ou componente de administração; o papel é fixado em <i>aluno</i> no servidor "
            "(rotas/auth.py:36-41 e app.py:316-321). Por isso a categoria não rende achados de "
            "“permissão no navegador”. O único achado associado é de lógica de negócio confiada ao "
            "cliente: <b>/api/responder</b> aceita <i>is_correct</i> do JSON (F-08).",
            "small",
        )
    )
    story.append(Spacer(1, 0.25 * cm))

    story.append(p("3.2 Limitações e cobertura", "h2"))
    limitations = [
        "As migrations de RLS não estão neste repositório. A verificação do SELECT aberto é documental "
        "(docs/banco_dados.md:27,38) e não substitui uma consulta ao dashboard/SQL de produção.",
        "Não foi executada nenhuma consulta contra a produção nem usado dado real de aluno; a auditoria "
        "é estática e baseada no código/documentação do repositório.",
        "O painel administrativo vive em repositório privado separado (gabaritei-admin) e ficou fora do "
        "escopo. Este repo não contém rotas administrativas nem UI de admin.",
        "Não há Docker, CI, Helm ou Terraform no repositório; a análise de deploy se limita ao Electron, "
        "PyInstaller, .env e site público.",
        "A ausência de sanitizador foi confirmada em requirements.txt/package.json; a exploração de "
        "cada sink depende do grau de confiança do conteúdo que chega até ele.",
    ]
    for item in limitations:
        story.append(p(f"• {item}", "body_left"))

    story.append(PageBreak())
    return story

# ---------------------------------------------------------------------------
# Seções 4 a 8
# ---------------------------------------------------------------------------


def build_strengths() -> list:
    story: list = [p("4. O que foi verificado e está correto", "h1")]
    story.append(
        p(
            "A auditoria não se limita a defeitos. Os controles abaixo foram conferidos no código, "
            "na documentação ou no histórico do repositório e estão corretos no estado atual. Eles "
            "reduzem o impacto de parte dos achados e devem ser preservados nas correções.",
            "body",
        )
    )
    rows = [
        [
            p("#", "table_head"),
            p("Controle verificado", "table_head"),
            p("Evidência", "table_head"),
            p("Por que importa", "table_head"),
        ]
    ]
    for i, (title, evidence, why) in enumerate(STRENGTHS, start=1):
        rows.append(
            [
                p(f"<b>{i}</b>", "table_cell_tight"),
                p(f"<b>{esc(title)}</b>", "table_cell_tight"),
                p(mono_wrap_files(evidence, 6.0), "table_cell_tight"),
                p(esc(why), "table_cell_tight"),
            ]
        )
    table = LongTable(rows, colWidths=[0.8 * cm, 3.9 * cm, 4.6 * cm, 7.7 * cm], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(rows)):
        style.append(("LINEBEFORE", (0, i), (0, i), 2.2, EMERALD))
    table.setStyle(TableStyle(style))
    story.append(table)
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        p(
            "Observação: a escrita do aluno exige <i>x-app-token</i> e identidade do dono segundo a "
            "documentação (evidência documental, não SQL executado). O CSRF é global e não há "
            "<i>csrf.exempt</i> no projeto; a única ressalva é que o token CSRF também fica legível "
            "por um XSS same-origin, o que reforça a prioridade de F-11.",
            "small",
        )
    )
    story.append(PageBreak())
    return story


def build_weaknesses() -> list:
    story: list = [p("5. Pontos fracos e risco sistêmico", "h1")]
    story.append(
        p(
            "Os pontos abaixo explicam por que os achados não são incidentes isolados: eles "
            "compartilham causa e se reforçam. A ordem reflete o risco percebido, não a ordem "
            "numérica dos achados.",
            "body",
        )
    )
    for sev, title, text in WEAKNESSES:
        color = SEVERITY_COLORS.get(sev, MUTED)
        head = Table(
            [[Chip(sev, color, width=1.95 * cm, height=0.5 * cm), p(f"<b>{esc(title)}</b>", "card_title")]],
            colWidths=[2.15 * cm, 14.35 * cm],
        )
        head.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        block = Table([[head], [p(esc(text), "card_text")]], colWidths=[16.5 * cm])
        block.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                    ("LINEBEFORE", (0, 0), (0, -1), 3, color),
                    ("LEFTPADDING", (0, 0), (-1, -1), 9),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(KeepTogether([block, Spacer(1, 0.22 * cm)]))
    story.append(PageBreak())
    return story


def build_findings_table() -> list:
    story: list = [p("6. Tabela de achados", "h1")]
    story.append(
        p(
            f"Os {len(FINDINGS)} achados confirmados estão ordenados por severidade e depois por "
            "categoria. A coluna <i>Local</i> aponta o arquivo e as linhas exatas; o detalhamento "
            "na seção 7 traz trecho, motivo de exploração e correção sugerida. Não há achado "
            "especulativo nesta tabela.",
            "body",
        )
    )
    rows = [
        [
            p("ID", "table_head"),
            p("Severidade", "table_head"),
            p("Cat.", "table_head"),
            p("Título", "table_head"),
            p("Local", "table_head"),
        ]
    ]
    sev_rank = {s: i for i, s in enumerate(SEVERITY_ORDER)}
    ordered = sorted(FINDINGS, key=lambda f: (sev_rank.get(f.severity, 9), f.category, f.fid))
    for f in ordered:
        rows.append(
            [
                p(f"<b>{f.fid}</b>", "table_cell"),
                Chip(f.severity, SEVERITY_COLORS[f.severity], width=1.78 * cm, height=0.46 * cm),
                p(f"<b>{f.category}</b>", "table_cell"),
                p(f"<b>{esc(f.title)}</b>", "table_cell_tight"),
                p(mono(f.location, 6.0), "mono_cell"),
            ]
        )
    table = LongTable(rows, colWidths=[1.15 * cm, 2.0 * cm, 1.0 * cm, 7.2 * cm, 5.65 * cm], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
    ]
    table.setStyle(TableStyle(style))
    story.append(table)
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        p(
            "<b>Legenda de categorias:</b> 1 — isolamento de inquilino/dono; 2 — permissão "
            "definida no navegador; 3 — IDOR; 4 — chaves expostas; 5 — inputs sem tratamento (XSS). "
            "<b>A categoria 2 não se aplica à UI administrativa</b> — não existe tela/rota de admin "
            "neste repositório e o papel é fixado em <i>aluno</i> no servidor; o único achado é de "
            "lógica de negócio confiada ao cliente.",
            "small",
        )
    )
    story.append(PageBreak())
    return story


def _finding_block(f) -> Table:
    color = SEVERITY_COLORS[f.severity]
    head = Table(
        [
            [
                Chip(f.severity, color, width=1.95 * cm, height=0.5 * cm),
                p(f"<b>{f.fid}</b> — {esc(f.title)}", "card_title"),
            ]
        ],
        colWidths=[2.15 * cm, 14.05 * cm],
    )
    head.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    body_parts = [p(f"<b>Local:</b> {mono(f.location, 6.5)}", "card_evidence")]
    snippet = TRECHOS.get(f.fid)
    if snippet:
        code = Table([[Preformatted(snippet, S["code"])]], colWidths=[15.6 * cm])
        code.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F1F5F9")),
                    ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
                    ("LINEBEFORE", (0, 0), (0, -1), 2, color),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        body_parts.append(code)
        body_parts.append(Spacer(1, 4))
    body_parts += [
        p(f"<b>Descrição.</b> {esc(f.description)}", "card_text"),
        p(f"<b>Por que é explorável / impacto.</b> {esc(f.impact)}", "card_text"),
        p(f"<b>Correção sugerida.</b> {esc(f.fix)}", "card_text"),
    ]
    if f.condicao:
        body_parts.append(p(f"<b>Condição de evidência.</b> <i>{esc(f.condicao)}</i>", "card_text"))
    block = Table([[head], [body_parts]], colWidths=[16.3 * cm])
    block.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WHITE),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 3, color),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return block


def build_findings_detail() -> list:
    story: list = [p("7. Detalhamento dos achados", "h1")]
    story.append(
        p(
            "Cada bloco traz a localização exata, a descrição verificada, o motivo de exploração, "
            "o impacto e a correção sugerida. Onde a evidência é documental, a condição está "
            "explícita. Trechos de código e nomes de tabelas aparecem em fonte monoespaçada.",
            "body",
        )
    )
    sev_rank = {s: i for i, s in enumerate(SEVERITY_ORDER)}
    ordered = sorted(FINDINGS, key=lambda f: (sev_rank.get(f.severity, 9), f.category, f.fid))
    for f in ordered:
        story.append(KeepTogether([_finding_block(f), Spacer(1, 0.28 * cm)]))
    story.append(PageBreak())
    return story


def build_recommendations() -> list:
    story: list = [p("8. Recomendações priorizadas", "h1")]
    story.append(
        p(
            "<b>P1</b> fecha exposição ativa ou integridade de dados e deve entrar antes do próximo "
            "build distribuído. <b>P2</b> reduz superfície e corrige defesa em profundidade. "
            "<b>P3</b> é sistêmico: testes, análise estática e governança de RLS para evitar regressão.",
            "body",
        )
    )
    rows = [
        [
            p("Prioridade", "table_head"),
            p("Ação", "table_head"),
            p("Como executar", "table_head"),
            p("Achados", "table_head"),
        ]
    ]
    p_color = {
        "P1": SEVERITY_COLORS["Crítica"],
        "P2": SEVERITY_COLORS["Média"],
        "P3": SEVERITY_COLORS["Baixa"],
    }
    for priority, action, description, findings in RECOMMENDATIONS:
        rows.append(
            [
                Chip(priority, p_color[priority], width=1.55 * cm, height=0.46 * cm),
                p(f"<b>{esc(action)}</b>", "table_cell_tight"),
                p(esc(description), "table_cell_tight"),
                p(mono(findings, 6.0), "mono_cell"),
            ]
        )
    table = LongTable(rows, colWidths=[1.9 * cm, 4.45 * cm, 8.1 * cm, 2.55 * cm], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    table.setStyle(TableStyle(style))
    story.append(table)
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        p(
            "Sequência sugerida: (1) fechar o SELECT e os IDORs; (2) eliminar o XSS e a rota "
            "legada; (3) reduzir exposição e sanear sinks; (4) institucionalizar testes e "
            "verificação de segredos. As issues da seção 10 já estão no formato de execução.",
            "small",
        )
    )
    story.append(PageBreak())
    return story


# ---------------------------------------------------------------------------
# Apêndice e issues
# ---------------------------------------------------------------------------


def build_routes_appendix() -> list:
    story: list = [p("9. Apêndice — Matriz de cobertura de rotas", "h1")]
    story.append(
        p(
            "Foram inventariadas 35 rotas que recebem identificador, mutam dados ou lidam com "
            "credenciais. A coluna <i>Controle</i> registra o filtro efetivamente presente no "
            "código, não a intenção documentada. <b>OK</b> significa que o dono é derivado da "
            "sessão; <b>IDOR</b> significa que o objeto é buscado apenas pelo ID recebido.",
            "body",
        )
    )
    rows = [
        [
            p("Rota", "table_head"),
            p("Arquivo:linha", "table_head"),
            p("Controle verificado", "table_head"),
            p("Status", "table_head"),
        ]
    ]
    for route, location, control, status in ROUTES:
        rows.append(
            [
                p(mono(route, 6.1), "table_cell_tight"),
                p(mono(location, 6.0), "mono_cell"),
                p(esc(control), "table_cell_tight"),
                p(f"<b>{esc(status.upper())}</b>", "table_head"),
            ]
        )
    table = LongTable(rows, colWidths=[5.5 * cm, 3.5 * cm, 5.3 * cm, 2.7 * cm], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.4),
    ]
    for i, (_, _, _, status) in enumerate(ROUTES, start=1):
        color = STATUS_COLORS.get(status, MUTED)
        style.append(("BACKGROUND", (3, i), (3, i), color))
    table.setStyle(TableStyle(style))
    story.append(table)
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        p(
            "Status <b>Risco latente</b>: o RLS owner-only de <i>editais_progresso</i> mitiga hoje, "
            "mas não há check de aplicação. <b>Exposição</b>: a rota é pública e devolve coluna "
            "sensível. <b>Falha de integridade</b>: o cliente influencia o placar. "
            "<b>Baixo</b>: referência cross-tenant sem impacto confirmado na listagem.",
            "small",
        )
    )
    story.append(PageBreak())
    return story


def build_issues() -> list:
    story: list = [p("10. ISSUES PARA O GITHUB", "h1")]
    story.append(
        p(
            "Os blocos abaixo estão completos e prontos para copiar e colar no GitHub. Cada issue "
            "começa com o título em Markdown, seguido de descrição, evidência, exploração, impacto, "
            "correção e critérios de aceite. O título do bloco e as labels sugeridas aparecem na "
            "faixa acima do texto; o conteúdo entre <b>--- ISSUE n ---</b> e <b>--- FIM ISSUE n ---</b> "
            "é o Markdown integral.",
            "body",
        )
    )
    story.append(
        Table(
            [
                [
                    p(
                        "<b>Como usar:</b> crie uma issue por bloco, cole o Markdown integral e "
                        "aplique as labels sugeridas. A ordem segue a prioridade: crítica, altas, "
                        "médias, baixas e hardening. Nove issues cobrem os quinze achados.",
                        "callout",
                    )
                ]
            ],
            colWidths=[17 * cm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), AMBER_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.8, HexColor("#FCD34D")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            ),
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    max_len = max((max((len(line) for line in issue["body"].splitlines()), default=0) for issue in ISSUES), default=0)
    # Courier avança 0.6 * fontSize por caractere; 17 cm = 481.9 pt.
    issue_size = min(8.0, max(6.8, (17 * cm - 18) / max(max_len, 1) / 0.6))
    issue_style = ParagraphStyle(
        "issue_dynamic",
        fontName=MONO,
        fontSize=issue_size,
        leading=issue_size * 1.28,
        textColor=TEXT,
        alignment=TA_LEFT,
        spaceAfter=0,
    )

    for index, issue in enumerate(ISSUES, start=1):
        story.append(CondPageBreak(4.6 * cm))
        story.append(
            Table(
                [[p(f"--- ISSUE {index} ---", "delim")]],
                colWidths=[17 * cm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#E2E8F0")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                ),
            )
        )
        title_bar = Table(
            [
                [p(f"<b>Issue {index}</b> — {esc(issue['title'])}", "issue_title")],
                [p(f"<font color='#CBD5E1'>Labels sugeridas: {esc(issue['labels'])}</font>", "cover_meta")],
            ],
            colWidths=[17 * cm],
        )
        title_bar.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), NAVY_2),
                    ("LEFTPADDING", (0, 0), (-1, -1), 9),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (0, 0), 7),
                    ("BOTTOMPADDING", (0, 0), (0, 0), 1),
                    ("TOPPADDING", (0, 1), (0, 1), 1),
                    ("BOTTOMPADDING", (0, 1), (0, 1), 7),
                ]
            )
        )
        story.append(title_bar)
        story.append(Spacer(1, 0.14 * cm))
        story.append(Preformatted(issue["body"], issue_style))
        story.append(Spacer(1, 0.2 * cm))
        story.append(
            Table(
                [[p(f"--- FIM ISSUE {index} ---", "delim")]],
                colWidths=[17 * cm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#E2E8F0")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                ),
            )
        )
        story.append(Spacer(1, 0.55 * cm))

    story.append(
        p(
            f"Fim do relatório. {len(FINDINGS)} achados verificados e {len(ISSUES)} issues "
            f"publicáveis. Documento gerado em {DATE_SHORT} por análise estática do repositório.",
            "small",
        )
    )
    return story


# ---------------------------------------------------------------------------
# Montagem do PDF
# ---------------------------------------------------------------------------


def build_pdf() -> Path:
    donut, bars = gerar_graficos()
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)

    doc = BaseDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Relatório de Auditoria de Segurança — Gabaritei Questões",
        author="Auditoria de Segurança",
        subject="Isolamento de dados, autorização, IDOR, segredos e XSS",
        creator="gerar_relatorio.py (reportlab)",
        keywords="segurança, auditoria, Flask, Supabase, Electron, IDOR, XSS, RLS",
    )

    cover_frame = Frame(2 * cm, 2.6 * cm, 17 * cm, 24.3 * cm, id="cover", showBoundary=0)
    body_frame = Frame(2 * cm, 2.05 * cm, 17 * cm, A4[1] - 2.05 * cm - 1.95 * cm, id="body", showBoundary=0)
    doc.addPageTemplates(
        [
            PageTemplate(id="Cover", frames=[cover_frame], onPage=draw_cover),
            PageTemplate(id="Body", frames=[body_frame], onPage=draw_body),
        ]
    )

    story: list = []
    story += build_cover()
    story += build_summary()
    story += build_charts(donut, bars)
    story += build_methodology()
    story += build_strengths()
    story += build_weaknesses()
    story += build_findings_table()
    story += build_findings_detail()
    story += build_recommendations()
    story += build_routes_appendix()
    story += build_issues()

    doc.build(story, canvasmaker=NumberedCanvas)
    return PDF_PATH


def main() -> None:
    pdf = build_pdf()
    size_kb = pdf.stat().st_size / 1024
    print(f"PDF gerado: {pdf}")
    print(f"Tamanho: {size_kb:.1f} KB")
    try:
        import pymupdf  # type: ignore

        with pymupdf.open(pdf) as document:
            print(f"Páginas: {document.page_count}")
    except Exception:
        pass
    print(f"Gráficos: {CHART_DIR / 'severidade.png'}")
    print(f"Gráficos: {CHART_DIR / 'categorias.png'}")


if __name__ == "__main__":
    main()
