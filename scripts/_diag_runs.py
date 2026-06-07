# -*- coding: utf-8 -*-
"""Diagnose run-level formatting (italic/bold/hyperlink) in the source docx files."""
import os
from docx import Document
from docx.oxml.ns import qn

ROOT = r"C:\Users\USER01\Dropbox\Workplace\D\George\PAPERS\Paroysiaseis\Cyprus 2025\ag-llm-stylometry"

def runs_of(p):
    """Walk all w:r under a paragraph (including inside w:hyperlink); report text + i/b + in-hyperlink."""
    out = []
    for r in p._p.iter(qn('w:r')):
        # text
        t = "".join(node.text or "" for node in r.iter(qn('w:t')))
        rpr = r.find(qn('w:rPr'))
        ital = bool(rpr is not None and rpr.find(qn('w:i')) is not None)
        bold = bool(rpr is not None and rpr.find(qn('w:b')) is not None)
        in_link = r.getparent().tag == qn('w:hyperlink')
        out.append((t, ital, bold, in_link))
    return out

def n_hyperlinks(p):
    return len(p._p.findall('.//' + qn('w:hyperlink')))

for fname in ["Ancient_Greek_LLM_Stylometry_Literature_Review.docx",
              "Ancient_Greek_LLM_Stylometry_Methods_Results.docx"]:
    print("="*80)
    print(fname)
    d = Document(os.path.join(ROOT, fname))
    # find a couple of reference paragraphs and one related-work body paragraph
    shown_ref = 0
    shown_body = 0
    in_refs = False
    for p in d.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue
        if txt.startswith("References"):
            in_refs = True
        if in_refs and shown_ref < 2 and (txt.startswith("Argamon") or txt.startswith("Burrows") or txt.startswith("Benjamini") or txt.startswith("Cohen")):
            print("\n[REF] style=", p.style.name, " hyperlinks=", n_hyperlinks(p))
            for (t, i, b, hl) in runs_of(p):
                print("   run i=%s b=%s link=%s : %r" % (i, b, hl, t[:70]))
            shown_ref += 1
        if (not in_refs) and shown_body < 1 and txt.startswith("Stylometry"):
            print("\n[BODY] style=", p.style.name, " hyperlinks=", n_hyperlinks(p))
            for (t, i, b, hl) in runs_of(p):
                print("   run i=%s b=%s link=%s : %r" % (i, b, hl, t[:70]))
            shown_body += 1
print("\nDONE")
