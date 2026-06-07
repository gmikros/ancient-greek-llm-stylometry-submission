# -*- coding: utf-8 -*-
"""Compare in-text citations in the Introduction vs the Related Work."""
import os, re
from docx import Document

ROOT = r"C:\Users\USER01\Dropbox\Workplace\D\George\PAPERS\Paroysiaseis\Cyprus 2025\ag-llm-stylometry"
doc = Document(os.path.join(ROOT, "Ancient_Greek_LLM_Stylometry_MERGED.docx"))

paras = [(p.style.name if p.style else "", p.text) for p in doc.paragraphs]

def section_text(start_pred, end_pred):
    buf, on = [], False
    for sn, t in paras:
        if not on and start_pred(sn, t):
            on = True
            continue
        if on and end_pred(sn, t):
            break
        if on:
            buf.append(t)
    return "\n".join(buf)

intro = section_text(lambda sn, t: sn == "Heading 1" and t.strip().startswith("1") and "Introduction" in t,
                     lambda sn, t: sn == "Heading 1" and t.strip().startswith("2"))
related = section_text(lambda sn, t: sn == "Heading 1" and t.strip().startswith("2") and "Related Work" in t,
                       lambda sn, t: sn == "Heading 1" and t.strip().startswith("3"))

# capture (first-author surname, year) keys
CIT = re.compile(r"([A-ZÄÖÜ][A-Za-zÀ-ÿ’'\-]+)(?:\s+(?:and\s+[A-ZÄÖÜ][A-Za-zÀ-ÿ’'\-]+|et\s+al\.))?\s+\(?(\d{4}[a-z]?)\)?")

def keys(text):
    out = set()
    for m in CIT.finditer(text):
        surname = re.sub(r"[’']s$", "", m.group(1))
        out.add("%s %s" % (surname, m.group(2)))
    return out

ki = keys(intro)
kr = keys(related)
overlap = sorted(ki & kr)
intro_only = sorted(ki - kr)
rel_only = sorted(kr - ki)

print("INTRO citations (%d):" % len(ki))
for k in sorted(ki):
    print("   ", k, " <-- also in RW" if k in kr else " <-- INTRO ONLY")
print()
print("RELATED WORK distinct citations: %d" % len(kr))
print()
print("OVERLAP (in BOTH): %d of %d intro cites (%.0f%%)" % (len(overlap), len(ki), 100*len(overlap)/max(1,len(ki))))
print("   ", ", ".join(overlap))
print()
print("INTRO-ONLY (not in RW): %d" % len(intro_only))
print("   ", ", ".join(intro_only) if intro_only else "(none)")
print()
print("RW-ONLY (cited in RW but NOT previewed in Intro): %d" % len(rel_only))
print("   ", ", ".join(rel_only))
