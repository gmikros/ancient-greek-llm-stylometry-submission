"""Extract text + tables + structure from the project's .docx files for review.

Writes one .txt per source .docx into scripts/_extracted/.
Preserves heading levels (via style name), lists, tables (pipe-delimited),
and notes the presence of inline images.
"""
import os
import sys
from docx import Document
from docx.oxml.ns import qn

ROOT = r"C:\Users\USER01\Dropbox\Workplace\D\George\PAPERS\Paroysiaseis\Cyprus 2025\ag-llm-stylometry"
OUT = os.path.join(ROOT, "scripts", "_extracted")
os.makedirs(OUT, exist_ok=True)

FILES = [
    "Ancient_Greek_LLM_Stylometry_Literature_Review.docx",
    "Ancient_Greek_LLM_Stylometry_Methods_Results.docx",
    "Ancient_Greek_LLM_Stylometry_Literature_Review_Verification.docx",
    os.path.join("output", "doc", "Ancient_Greek_LLM_Stylometry.docx"),
]

def iter_block_items(parent):
    """Yield paragraphs and tables in document order."""
    from docx.document import Document as _Doc
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    if isinstance(parent, _Doc):
        parent_elm = parent.element.body
    else:
        parent_elm = parent._tc
    for child in parent_elm.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)

def para_text(p):
    txt = p.text
    # detect inline images
    has_img = bool(p._p.findall('.//' + qn('w:drawing'))) or bool(p._p.findall('.//' + qn('w:pict')))
    return txt, has_img

def render_table(tbl):
    rows = []
    for row in tbl.rows:
        cells = []
        for c in row.cells:
            cells.append(" ".join(c.text.split()))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)

for f in FILES:
    src = os.path.join(ROOT, f)
    if not os.path.exists(src):
        print("MISSING:", src)
        continue
    try:
        doc = Document(src)
    except Exception as e:
        print("ERROR opening", src, e)
        continue
    base = os.path.splitext(os.path.basename(f))[0]
    out_path = os.path.join(OUT, base + ".txt")
    n_img = 0
    n_tbl = 0
    with open(out_path, "w", encoding="utf-8") as w:
        w.write("# SOURCE: %s\n\n" % f)
        for block in iter_block_items(doc):
            cls = block.__class__.__name__
            if cls == "Paragraph":
                txt, has_img = para_text(block)
                style = block.style.name if block.style else ""
                if has_img:
                    n_img += 1
                    w.write("[[IMAGE]]\n")
                if txt.strip() == "" and not has_img:
                    continue
                if style and ("Heading" in style or "Title" in style):
                    w.write("\n%s [%s]\n" % (txt, style))
                else:
                    prefix = ""
                    if style and "List" in style:
                        prefix = "- "
                    w.write(prefix + txt + "\n")
            else:  # Table
                n_tbl += 1
                w.write("\n[TABLE %d]\n" % n_tbl)
                w.write(render_table(block) + "\n\n")
    print("WROTE:", out_path, "| paragraphs+tables rendered |", "images:", n_img, "tables:", n_tbl)

print("DONE")
