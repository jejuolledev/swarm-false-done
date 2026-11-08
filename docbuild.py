"""Fill the official Apart template (docx) with our content. Formatting is cloned from the
template's own paragraphs so headings and body text keep the template look."""
import copy, re
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
FONT = "Old Standard TT"


class Report:
    def __init__(self, template):
        self.d = docx.Document(template)
        ps = self.d.paragraphs
        self.proto = {"h2": copy.deepcopy(ps[2]._p), "h3": copy.deepcopy(ps[47]._p),
                      "body": copy.deepcopy(ps[3]._p)}
        body = self.d.element.body
        info_tbl = self.d.tables[1]._tbl
        # drop everything after the title table except the final sectPr
        kids = list(body)
        start = kids.index(self.d.tables[0]._tbl) + 1
        for el in kids[start:]:
            if el.tag != W + "sectPr":
                body.remove(el)
        self.body = body
        self.sect = body.find(W + "sectPr")

    # ---------------------------------------------------------------- header block
    def header(self, title, author, affil_lines, abstract):
        t0 = self.d.tables[0]
        tp = [p for p in t0.rows[0].cells[0].paragraphs if p.text.strip()][0]
        tp.runs[0].text = title
        cell = t0.rows[1].cells[0]
        author_tbl, abs_tbl = cell.tables[0], cell.tables[1]
        # replace the 6-slot author grid with plain centred lines
        anchor = author_tbl._tbl
        lines = [(author, True)] + [(l, False) for l in affil_lines] + [("", False), ("With", True), ("Apart Research", False)]
        for text, bold in lines:
            p = OxmlElement("w:p")
            anchor.addprevious(p)
            para = docx.text.paragraph.Paragraph(p, cell)
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.paragraph_format.space_after = Pt(0)
            r = para.add_run(text); self._font(r, 11, bold=bold)
        anchor.getparent().remove(anchor)
        # widen the abstract box to the text width so that the headline figure fits on page 1
        for el in abs_tbl._tbl.iter():
            if el.tag in (W + "tblW", W + "tcW"):
                el.set(qn("w:w"), "9000"); el.set(qn("w:type"), "dxa")
            elif el.tag == W + "gridCol":
                el.set(qn("w:w"), "9000")
            elif el.tag == W + "tblInd":
                el.set(qn("w:w"), "180")
        ap = abs_tbl.rows[0].cells[0].paragraphs[0]
        for r in ap.runs[1:]:
            r._r.getparent().remove(r._r)
        # tighten blank spacer paragraphs in the title block (template look kept)
        for row in t0.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    if not p.text.strip() and not p._p.findall(".//" + W + "footnoteReference"):
                        p.paragraph_format.space_after = Pt(0); p.paragraph_format.space_before = Pt(0)
                        for r in p.runs:
                            r.font.size = Pt(4)
        ap.runs[0].text = abstract
        ap.runs[0].font.size = Pt(9.5)
        ap.runs[0].italic = False
        ap.runs[0].underline = False
        ap.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for extra in abs_tbl.rows[0].cells[0].paragraphs[1:]:
            for r in extra.runs:
                r.text = ""

    # ---------------------------------------------------------------- helpers
    def _font(self, r, size, bold=False, italic=False, mono=False):
        r.bold, r.italic = bold, italic
        r.font.size = Pt(size)
        name = "Courier New" if mono else FONT
        r.font.name = name
        rpr = r._r.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
        for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rf.set(qn(a), name)

    def _clone(self, kind):
        p = copy.deepcopy(self.proto[kind])
        for r in p.findall(W + "r"):
            p.remove(r)
        for b in p.findall(W + "bookmarkStart") + p.findall(W + "bookmarkEnd"):
            p.remove(b)
        self.sect.addprevious(p)
        return docx.text.paragraph.Paragraph(p, self.d._body)

    def h2(self, text):
        p = self._clone("h2"); r = p.add_run(text); self._font(r, 14, bold=True)
        r.font.color.rgb = RGBColor(0x43, 0x43, 0x43)
        return p

    def h3(self, text):
        p = self._clone("h3"); r = p.add_run(text); self._font(r, 12, bold=True)
        r.font.color.rgb = RGBColor(0x43, 0x43, 0x43)
        return p

    def para(self, text, size=10.5, indent=0.0, space_after=4, align="justify", mono=False):
        """**bold** and *italic* markup is supported."""
        p = self._clone("body")
        pf = p.paragraph_format
        pf.space_before = Pt(0); pf.space_after = Pt(space_after)
        pf.line_spacing = 1.08 if not mono else 1.0
        if indent:
            pf.left_indent = Inches(indent)
        p.alignment = {"justify": WD_ALIGN_PARAGRAPH.JUSTIFY, "left": WD_ALIGN_PARAGRAPH.LEFT,
                       "center": WD_ALIGN_PARAGRAPH.CENTER}[align]
        for tok in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
            if not tok:
                continue
            if tok.startswith("**"):
                r = p.add_run(tok[2:-2]); self._font(r, size, bold=True, mono=mono)
            elif tok.startswith("*"):
                r = p.add_run(tok[1:-1]); self._font(r, size, italic=True, mono=mono)
            else:
                r = p.add_run(tok); self._font(r, size, mono=mono)
        return p

    def code(self, text, size=7.5):
        for line in text.split("\n"):
            self.para(line if line else " ", size=size, indent=0.15, space_after=0, align="left", mono=True)
        self.para(" ", size=4, space_after=2)

    def figure(self, path, width_in, caption):
        p = self._clone("body"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2); p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(path, width=Inches(width_in))
        self.para(caption, size=9, align="justify", space_after=8)

    def table(self, header, rows, widths, caption, size=8.5):
        self.para(caption, size=9, align="justify", space_after=3).paragraph_format.keep_with_next = True
        t = self.d.add_table(rows=1 + len(rows), cols=len(header))
        self.sect.addprevious(t._tbl)
        t.autofit = False
        grid = t._tbl.tblGrid
        for gc, wd in zip(grid.findall(qn("w:gridCol")), widths):
            gc.set(qn("w:w"), str(int(wd * 1440)))
        tblPr = t._tbl.tblPr
        lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "bottom", "insideH"):
            e = OxmlElement(f"w:{edge}")
            e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), "999999")
            borders.append(e)
        tblPr.append(borders)
        trPr = t.rows[0]._tr.get_or_add_trPr()
        th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
        for i, row in enumerate([header] + rows):
            for j, val in enumerate(row):
                c = t.cell(i, j); c.width = Inches(widths[j])
                pp = c.paragraphs[0]
                pp.paragraph_format.space_after = Pt(0); pp.paragraph_format.space_before = Pt(0)
                pp.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
                r = pp.add_run(str(val)); self._font(r, size, bold=(i == 0))
        self.para(" ", size=4, space_after=4)
        return t

    def takeaway(self, text, label="What to do: "):
        """One-line coloured takeaway box (navy fill, white text)."""
        t = self.d.add_table(rows=1, cols=1)
        self.sect.addprevious(t._tbl)
        t.autofit = False
        c = t.cell(0, 0); c.width = Inches(6.5)
        tcPr = c._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "1F2A44")
        tcPr.append(shd)
        mar = OxmlElement("w:tcMar")
        for side in ("top", "bottom", "left", "right"):
            e = OxmlElement(f"w:{side}"); e.set(qn("w:w"), "110" if side in ("top", "bottom") else "160"); e.set(qn("w:type"), "dxa")
            mar.append(e)
        tcPr.append(mar)
        pp = c.paragraphs[0]
        pp.paragraph_format.space_after = Pt(0); pp.paragraph_format.space_before = Pt(0)
        r = pp.add_run(label); self._font(r, 9.5, bold=True); r.font.color.rgb = RGBColor(0xF2, 0x9A, 0x6B)
        r = pp.add_run(text); self._font(r, 9.5, bold=False); r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        self.para(" ", size=3, space_after=2)

    def claim(self, text):
        """Claim-style result heading: a sentence that states the finding."""
        p = self._clone("h3"); r = p.add_run(text); self._font(r, 11.5, bold=True)
        r.font.color.rgb = RGBColor(0x1F, 0x2A, 0x44)
        p.paragraph_format.space_before = Pt(10); p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        return p

    def page_break(self):
        p = self._clone("body")
        r = p.add_run(); br = OxmlElement("w:br"); br.set(qn("w:type"), "page"); r._r.append(br)

    def save(self, path):
        self.d.save(path)
