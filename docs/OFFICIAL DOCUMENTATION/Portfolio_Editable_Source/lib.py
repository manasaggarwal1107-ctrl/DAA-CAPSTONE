"""Layout library for the Mini Courier Planner screenshot portfolio.

Everything visual lives here (fonts, styles, figure blocks, header/footer, TOC).
Content lives in build_portfolio.py.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, Flowable, PageBreak,
                                NextPageTemplate, CondPageBreak, KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents

# ---------------------------------------------------------------- fonts
FD = "/usr/share/fonts/truetype/"
pdfmetrics.registerFont(TTFont("Body", FD + "crosextra/Carlito-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Body-B", FD + "crosextra/Carlito-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Body-I", FD + "crosextra/Carlito-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Body-BI", FD + "crosextra/Carlito-BoldItalic.ttf"))
pdfmetrics.registerFont(TTFont("Mono", FD + "dejavu/DejaVuSansMono.ttf"))
pdfmetrics.registerFont(TTFont("Mono-B", FD + "dejavu/DejaVuSansMono-Bold.ttf"))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-B",
                              italic="Body-I", boldItalic="Body-BI")
pdfmetrics.registerFontFamily("Mono", normal="Mono", bold="Mono-B",
                              italic="Mono", boldItalic="Mono-B")

# ---------------------------------------------------------------- palette
INK = HexColor("#0F172A")
MUTED = HexColor("#475569")
FAINT = HexColor("#94A3B8")
RULE = HexColor("#CBD5E1")
PANEL = HexColor("#F1F5F9")
PANEL2 = HexColor("#F8FAFC")
ACCENT = HexColor("#0E7490")
ACCENT_L = HexColor("#E0F2F7")
KIND = {  # evidence-type tags
    "SCREENSHOT": HexColor("#0E7490"),
    "MEASURED DATA": HexColor("#15803D"),
    "EXPLANATORY DIAGRAM": HexColor("#6D28D9"),
    "SAMPLE INPUT": HexColor("#B45309"),
    "UI SCREENSHOT, SEGMENTED": HexColor("#0E7490"),
}

PAGE_W, PAGE_H = A4
MX = 16 * mm
CONTENT_W = PAGE_W - 2 * MX
TOP = 24 * mm
BOT = 20 * mm
FRAME_H = PAGE_H - TOP - BOT

# ---------------------------------------------------------------- styles
def S(name, **kw):
    base = dict(fontName="Body", fontSize=9.8, leading=14, textColor=INK,
                alignment=TA_LEFT, spaceAfter=0)
    base.update(kw)
    return ParagraphStyle(name, **base)

ST = {
    "body": S("body", spaceAfter=5),
    "lead": S("lead", fontSize=11, leading=15.5, textColor=MUTED, spaceAfter=6),
    "small": S("small", fontSize=8.4, leading=11.4, textColor=MUTED),
    "cap": S("cap", fontSize=8.7, leading=11.8, textColor=MUTED),
    "figtitle": S("figtitle", fontName="Body-B", fontSize=10.6, leading=13),
    "H1": S("H1", fontName="Body-B", fontSize=21, leading=25, spaceAfter=6),
    "H2": S("H2", fontName="Body-B", fontSize=13.5, leading=17, spaceBefore=10, keepWithNext=1,
            spaceAfter=4, textColor=INK),
    "H3": S("H3", fontName="Body-B", fontSize=10.4, leading=13.5, spaceBefore=6, keepWithNext=1,
            spaceAfter=2, textColor=ACCENT),
    "bullet": S("bullet", leftIndent=11, bulletIndent=1, spaceAfter=2.4),
    "cell": S("cell", fontSize=8.6, leading=11),
    "cellb": S("cellb", fontName="Body-B", fontSize=8.6, leading=11),
    "cellh": S("cellh", fontName="Body-B", fontSize=8.2, leading=10.4,
               textColor=colors.white),
    "cellr": S("cellr", fontSize=8.6, leading=11, alignment=2),
    "cellrh": S("cellrh", fontName="Body-B", fontSize=8.2, leading=10.4,
                textColor=colors.white, alignment=2),
    "mono": S("mono", fontName="Mono", fontSize=7.6, leading=10),
    "note": S("note", fontSize=8.8, leading=12, textColor=HexColor("#78350F")),
    "toc1": S("toc1", fontName="Body-B", fontSize=10.4, leading=15, spaceBefore=3),
    "toc2": S("toc2", fontSize=9.4, leading=13, leftIndent=12, textColor=MUTED),
    "lof": S("lof", fontSize=9.2, leading=13, textColor=INK),
}


def P(text, style="body"):
    return Paragraph(text, ST[style])


def bullets(items, style="bullet"):
    return [Paragraph(t, ST[style], bulletText="\u2022") for t in items]


# ---------------------------------------------------------------- flowables
class Rule(Flowable):
    def __init__(self, width=CONTENT_W, color=RULE, thick=0.6, space=4):
        super().__init__()
        self.w, self.c, self.t, self.sp = width, color, thick, space

    def wrap(self, aw, ah):
        return self.w, self.sp * 2

    def draw(self):
        self.canv.setStrokeColor(self.c)
        self.canv.setLineWidth(self.t)
        self.canv.line(0, self.sp, self.w, self.sp)


class SectionHead(Paragraph):
    """H1 with small numeric kicker; registers in TOC."""
    def __init__(self, num, title):
        super().__init__(f'<font color="#0E7490" size="11">SECTION {num}</font><br/>{title}',
                         ST["H1"])
        self._toc = (0, f"{num}.  {title}")


class SubHead(Paragraph):
    def __init__(self, text, level=1, style="H2"):
        super().__init__(text, ST[style])
        self._toc = (level, text) if level is not None else None


def note_box(text, label="EVIDENCE NOTE"):
    p = Paragraph(f'<b>{label}.</b> {text}', ST["note"])
    t = Table([[p]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#FEF7E6")),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, HexColor("#D97706")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def info_box(text, label=None):
    txt = f"<b>{label}.</b> {text}" if label else text
    p = Paragraph(txt, ST["small"])
    t = Table([[p]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT_L),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, ACCENT),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def data_table(rows, col_widths, header_rows=1, align_right=(), zebra=True,
               font_size=None, bold_first_col=False, total_row=False):
    """rows: list of lists of str/Paragraph. First row(s) are header."""
    out = []
    for ri, row in enumerate(rows):
        r = []
        for ci, c in enumerate(row):
            if isinstance(c, Flowable):
                r.append(c)
                continue
            hdr = ri < header_rows
            right = ci in align_right
            if hdr:
                st = "cellrh" if right else "cellh"
            elif bold_first_col and ci == 0:
                st = "cellb"
            elif total_row and ri == len(rows) - 1:
                st = "cellb" if not right else "cellr"
            else:
                st = "cellr" if right else "cell"
            r.append(Paragraph(str(c), ST[st]))
        out.append(r)
    t = Table(out, colWidths=col_widths, repeatRows=header_rows)
    style = [
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), HexColor("#1E293B")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
        ("LINEBELOW", (0, header_rows), (-1, -1), 0.4, RULE),
        ("BOX", (0, 0), (-1, -1), 0.6, RULE),
    ]
    if zebra:
        for i in range(header_rows, len(out)):
            if (i - header_rows) % 2 == 1:
                style.append(("BACKGROUND", (0, i), (-1, i), PANEL2))
    if total_row:
        style += [("BACKGROUND", (0, len(out) - 1), (-1, len(out) - 1), PANEL),
                  ("LINEABOVE", (0, len(out) - 1), (-1, len(out) - 1), 0.8, MUTED)]
    t.setStyle(TableStyle(style))
    return t


def table_caption(num, text):
    return Paragraph(f'<font name="Body-B" color="#0E7490">Table {num}</font>'
                     f'&nbsp;&nbsp;{text}', ST["cap"])


class FigureBlock(Flowable):
    """Evidence figure: tag + numbered title, framed image(s), caption.
    Aspect ratio always preserved; size is deterministic (does not depend on
    the space left on the page, so nothing is ever shrunk to fit)."""
    def __init__(self, num, title, kind, images, caption, maxh, maxw=CONTENT_W,
                 seg_labels=None, seg_gap=5 * mm):
        super().__init__()
        self.num, self.title, self.kind = num, title, kind
        self.paths = images if isinstance(images, (list, tuple)) else [images]
        self.caption_text = caption
        self.maxh, self.maxw = maxh, maxw
        self.seg_labels = seg_labels
        self.seg_gap = seg_gap
        self._lof = (0, f"Figure {num}  \u2013  {title}")
        self.imgs = [ImageReader(p) for p in self.paths]
        self.sizes = [im.getSize() for im in self.imgs]
        self.head_h = 7.5 * mm
        self.pad = 1.2 * mm

    def _layout(self):
        if len(self.imgs) == 1:
            iw, ih = self.sizes[0]
            s = min(self.maxw / iw, self.maxh / ih)
            self.dims = [(iw * s, ih * s)]
        else:  # side-by-side segments, same width
            n = len(self.imgs)
            w = (self.maxw - self.seg_gap * (n - 1)) / n
            dims = [(w, w * ih / iw) for iw, ih in self.sizes]
            tallest = max(d[1] for d in dims)
            if tallest > self.maxh:
                f = self.maxh / tallest
                dims = [(d[0] * f, d[1] * f) for d in dims]
            self.dims = dims

    def wrap(self, aw, ah):
        self._layout()
        img_w = (sum(d[0] for d in self.dims) +
                 (self.seg_gap * (len(self.dims) - 1) if len(self.dims) > 1 else 0))
        self.cap = Paragraph(self.caption_text, ST["cap"])
        self.cw = CONTENT_W
        _, ch = self.cap.wrap(self.cw, 1000)
        self.cap_h = ch
        lab = 4.5 * mm if self.seg_labels else 0
        self.lab_h = lab
        self.img_h = max(d[1] for d in self.dims)
        self.total_w = CONTENT_W
        self.h = (self.head_h + lab + self.img_h + 2 * self.pad + 2.5 * mm
                  + self.cap_h + 1 * mm)
        return CONTENT_W, self.h

    def draw(self):
        c = self.canv
        top = self.h
        # tag chip
        tag = self.kind
        c.setFont("Body-B", 6.8)
        tw = pdfmetrics.stringWidth(tag, "Body-B", 6.8) + 8
        col = KIND.get(tag, ACCENT)
        c.setFillColor(col)
        c.roundRect(0, top - 5.6 * mm, tw, 4.4 * mm, 1.2, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.drawString(4, top - 4.15 * mm, tag)
        # title
        c.setFillColor(INK)
        c.setFont("Body-B", 10.6)
        c.drawString(tw + 8, top - 4.35 * mm,
                     f"Figure {self.num}  \u2014  {self.title}")
        y = top - self.head_h - self.lab_h
        x = 0
        if len(self.dims) == 1:
            w, h = self.dims[0]
            x = (CONTENT_W - w) / 2 if w < CONTENT_W - 1 else 0
            self._img(c, self.imgs[0], x, y - h - self.pad * 2, w, h)
            y = y - h - 2 * self.pad
        else:
            total = sum(d[0] for d in self.dims) + self.seg_gap * (len(self.dims) - 1)
            x = (CONTENT_W - total) / 2
            for i, (im, (w, h)) in enumerate(zip(self.imgs, self.dims)):
                if self.seg_labels:
                    c.setFillColor(MUTED)
                    c.setFont("Body-B", 7.4)
                    c.drawString(x, top - self.head_h - 3.2 * mm, self.seg_labels[i])
                self._img(c, im, x, y - h - self.pad * 2, w, h)
                x += w + self.seg_gap
            y = y - self.img_h - 2 * self.pad
        self.cap.drawOn(c, 0, y - 2.5 * mm - self.cap_h)

    def _img(self, c, im, x, y, w, h):
        pad = self.pad
        c.setFillColor(PANEL)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.6)
        c.rect(x, y, w + 2 * pad, h + 2 * pad, stroke=1, fill=1)
        c.drawImage(im, x + pad, y + pad, w, h, mask=None)


# ---------------------------------------------------------------- doc template
class Portfolio(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, pagesize=A4, leftMargin=MX, rightMargin=MX,
                         topMargin=TOP, bottomMargin=BOT, **kw)
        cover_frame = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=0, rightPadding=0,
                            topPadding=0, bottomPadding=0, id="cover")
        body_frame = Frame(MX, BOT, CONTENT_W, FRAME_H, leftPadding=0, rightPadding=0,
                           topPadding=0, bottomPadding=0, id="body")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover_frame], onPage=draw_cover),
            PageTemplate(id="body", frames=[body_frame], onPage=draw_chrome),
        ])
        self._bm = 0

    def afterFlowable(self, f):
        t = getattr(f, "_toc", None)
        if t:
            level, text = t
            self.notify("TOCEntry", (level, text, self.page))
            key = f"bm{self._bm}"; self._bm += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text.replace("&amp;", "&"), key, level, closed=False)
        l = getattr(f, "_lof", None)
        if l:
            self.notify("LOFEntry", l + (self.page,))


class ListOfFigures(TableOfContents):
    def notify(self, kind, stuff):
        if kind == "LOFEntry":
            self.addEntry(*stuff)


def draw_chrome(c, doc):
    c.saveState()
    # header
    c.setStrokeColor(RULE)
    c.setLineWidth(0.6)
    c.line(MX, PAGE_H - 15 * mm, PAGE_W - MX, PAGE_H - 15 * mm)
    c.setFont("Body-B", 8.4)
    c.setFillColor(INK)
    c.drawString(MX, PAGE_H - 12.2 * mm, "MINI COURIER PLANNER")
    w = pdfmetrics.stringWidth("MINI COURIER PLANNER", "Body-B", 8.4)
    c.setFont("Body", 8.4)
    c.setFillColor(MUTED)
    c.drawString(MX + w + 6, PAGE_H - 12.2 * mm, "Project Screenshot Portfolio")
    c.drawRightString(PAGE_W - MX, PAGE_H - 12.2 * mm, "DAA  \u00b7  ETCCDA302")
    # accent tick
    c.setFillColor(ACCENT)
    c.rect(MX, PAGE_H - 15.5 * mm, 14 * mm, 1.0, stroke=0, fill=1)
    # footer
    c.setStrokeColor(RULE)
    c.line(MX, 14 * mm, PAGE_W - MX, 14 * mm)
    c.setFont("Body", 8.2)
    c.setFillColor(MUTED)
    c.drawString(MX, 9.6 * mm, "Manas Aggarwal  \u00b7  B.Tech CSE (AI/ML)  \u00b7  K.R. Mangalam University")
    c.setFont("Body-B", 8.6)
    c.setFillColor(INK)
    c.drawRightString(PAGE_W - MX, 9.6 * mm, f"Page {doc.page}")
    c.restoreState()


def draw_cover(c, doc):
    c.saveState()
    # left accent band
    c.setFillColor(INK)
    c.rect(0, 0, 11 * mm, PAGE_H, stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.rect(11 * mm, 0, 1.6 * mm, PAGE_H, stroke=0, fill=1)
    # faint dot grid (top-right) \u2013 abstract, not an interface
    c.setFillColor(HexColor("#CBD5E1"))
    for i in range(14):
        for j in range(11):
            c.circle(PAGE_W - 22 * mm - i * 6.2 * mm, PAGE_H - 22 * mm - j * 6.2 * mm,
                     0.7, stroke=0, fill=1)
    c.restoreState()
