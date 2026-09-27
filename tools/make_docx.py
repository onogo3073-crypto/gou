"""Markdown風テキストを社内書式のWordに変換します。

使い方: python3 tools/make_docx.py 入力.md 出力.docx

書式: MSゴシック10pt・行間狭め・表は縞模様、金額は右寄せ、年度・見出し行は中央。
対応記法: # 見出し / ## / ### 、- 箇条書き、1. 番号付き、| 表 |、空行で段落区切り、**太字**
"""
import re
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

FONT = "ＭＳ ゴシック"
SIZE = Pt(10)
HEADER_FILL = "1F3864"
ZEBRA_FILL = "EEF2F7"

AMOUNT = re.compile(r"^[▲△\-+]?[¥￥]?\s*[\d,]+(\.\d+)?\s*(円|千円|万円|百万円|%|％|人|名|件|回)?$")
YEAR = re.compile(r"^(\d{4}|令和\s*\d+|R\d+|平成\s*\d+)\s*(年度?|期)?(\s*\d{1,2}月(\d{1,2}日)?)?$")


def set_font(run, bold=False, size=SIZE, color=None):
    run.font.name = FONT
    run.font.size = size
    run.font.bold = bold
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def tight(paragraph, before=0, after=2):
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.line_spacing_rule = WD_LINE_SPACING.SINGLE


def add_inline(paragraph, text, bold=False, size=SIZE, color=None):
    for i, part in enumerate(re.split(r"\*\*", text)):
        if part:
            set_font(paragraph.add_run(part), bold=bold or i % 2 == 1, size=size, color=color)


def shade(cell, fill):
    tc_pr = cell._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def cell_align(text):
    t = text.strip()
    if YEAR.match(t):
        return WD_ALIGN_PARAGRAPH.CENTER
    if AMOUNT.match(t):
        return WD_ALIGN_PARAGRAPH.RIGHT
    return WD_ALIGN_PARAGRAPH.LEFT


def add_table(doc, rows):
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            cell = table.cell(r, c)
            p = cell.paragraphs[0]
            tight(p, after=0)
            if r == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_inline(p, text, bold=True, color="FFFFFF")
                shade(cell, HEADER_FILL)
            else:
                p.alignment = cell_align(text)
                add_inline(p, text)
                if r % 2 == 0:
                    shade(cell, ZEBRA_FILL)
    tight(doc.add_paragraph(), after=0)


def parse_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def convert(src, dst):
    doc = Document()
    for section in doc.sections:
        section.top_margin = section.bottom_margin = Mm(20)
        section.left_margin = section.right_margin = Mm(20)
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = SIZE
    normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)

    lines = open(src, encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                if not re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", lines[i]):
                    rows.append(parse_row(lines[i]))
                i += 1
            width = max(len(r) for r in rows)
            add_table(doc, [r + [""] * (width - len(r)) for r in rows])
            continue
        heading = re.match(r"^(#{1,3})\s+(.*)", line)
        if heading:
            level = len(heading.group(1))
            p = doc.add_paragraph()
            tight(p, before=6 if level > 1 else 0, after=3)
            if level == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_inline(p, heading.group(2), bold=True, size=Pt({1: 14, 2: 12, 3: 10.5}[level]), color="1F3864")
        elif re.match(r"^\s*[-・]\s+", line):
            p = doc.add_paragraph(style="List Bullet")
            tight(p, after=0)
            add_inline(p, re.sub(r"^\s*[-・]\s+", "", line))
        elif re.match(r"^\s*\d+\.\s+", line):
            p = doc.add_paragraph(style="List Number")
            tight(p, after=0)
            add_inline(p, re.sub(r"^\s*\d+\.\s+", "", line))
        elif line.strip():
            p = doc.add_paragraph()
            tight(p)
            add_inline(p, line.strip())
        i += 1
    doc.save(dst)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("使い方: python3 tools/make_docx.py 入力.md 出力.docx")
    convert(sys.argv[1], sys.argv[2])
    print(f"作成しました: {sys.argv[2]}")
