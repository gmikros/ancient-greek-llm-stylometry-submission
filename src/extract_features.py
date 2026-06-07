"""Chunk-level stylometric feature extraction for Ancient Greek.

Backend: Stanza `grc` PROIEL (installed in this environment), mirroring the
column scheme of the legacy extractor (pos_*, case_*, tense_*, aspect_*, mood_*,
gender_*, dep_rel_*) plus lexical-diversity (L_*), entropy, and basic counts.
This produces one row per text (chunk), with the Category1-4 + extended-id
schema the analysis library expects.

Usage:
    # Build a corpus manifest spanning Human + all generated conditions, then:
    python src/extract_features.py --corpus data/features/corpus_manifest.csv \
        --out data/features/features_chunklevel.csv
    python src/extract_features.py ... --limit 20    # smoke test
"""
from __future__ import annotations

import argparse
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import config  # noqa: E402
from src.chunking import word_tokens  # noqa: E402
from src.normalize import normalize_greek  # noqa: E402

# Feature key universes (kept fixed so every row has the same columns).
POS_TAGS = ["ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM",
            "PART", "PRON", "PROPN", "PUNCT", "SCONJ", "VERB", "X"]
CASES = ["Nom", "Gen", "Dat", "Acc", "Voc"]
TENSES = ["Pres", "Past", "Fut"]
ASPECTS = ["Imp", "Perf", "Aor"]
MOODS = ["Ind", "Sub", "Imp", "Opt"]
GENDERS = ["Masc", "Fem", "Neut"]
DEPRELS = ["nsubj", "obj", "iobj", "obl", "advmod", "amod", "nmod", "det",
           "case", "cc", "conj", "mark", "advcl", "acl", "ccomp", "xcomp",
           "cop", "aux", "root", "punct", "appos", "parataxis", "fixed", "flat"]

_PIPELINE = None


def _get_pipeline():
    global _PIPELINE
    if _PIPELINE is None:
        import stanza
        try:
            _PIPELINE = stanza.Pipeline(
                lang=config.STANZA_LANG, package=config.STANZA_PACKAGE,
                processors="tokenize,pos,lemma,depparse",
                verbose=False, download_method=None)
        except Exception:
            stanza.download(config.STANZA_LANG, package=config.STANZA_PACKAGE, verbose=False)
            _PIPELINE = stanza.Pipeline(
                lang=config.STANZA_LANG, package=config.STANZA_PACKAGE,
                processors="tokenize,pos,lemma,depparse", verbose=False)
    return _PIPELINE


# --- Lexical diversity / entropy (backend-independent) ----------------------
def _entropy(counts) -> float:
    total = sum(counts)
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counts if c)


def _mtld(tokens, threshold=0.72) -> float:
    def _one_pass(seq):
        factors, types, n = 0, set(), 0
        for t in seq:
            types.add(t); n += 1
            if n > 0 and (len(types) / n) <= threshold:
                factors += 1; types, n = set(), 0
        if n > 0:
            factors += (1 - (len(types) / n)) / (1 - threshold)
        return len(seq) / factors if factors else len(seq)
    if len(tokens) < 10:
        return float(len(set(tokens)))
    return (_one_pass(tokens) + _one_pass(tokens[::-1])) / 2.0


def lexical_features(tokens: list[str]) -> dict:
    n = len(tokens)
    types = set(tokens)
    v = len(types)
    freqs = Counter(tokens)
    hapax = sum(1 for w, c in freqs.items() if c == 1)
    ttr = v / n if n else 0.0
    return {
        "n_tokens": n, "n_types": v, "hapax_legomena": hapax,
        "L_TTR": ttr,
        "L_Root_TTR": v / math.sqrt(n) if n else 0.0,
        "L_Log_TTR": (math.log(v) / math.log(n)) if n > 1 and v > 0 else 0.0,
        "L_MTLD": _mtld(tokens),
        "text_entropy": _entropy(list(freqs.values())),
        "avg_word_length": float(np.mean([len(t) for t in tokens])) if tokens else 0.0,
    }


def _safe_prop(counter: Counter, keys: list[str], total: int, prefix: str) -> dict:
    return {f"{prefix}{k}": (counter.get(k, 0) / total if total else 0.0) for k in keys}


def extract_one(text: str) -> dict:
    toks = word_tokens(text)
    feats = lexical_features(toks)

    nlp = _get_pipeline()
    doc = nlp(text)
    pos_c, case_c, tense_c, asp_c, mood_c, gen_c, dep_c = (Counter() for _ in range(7))
    n_words_tagged = 0
    n_sents = len(doc.sentences)
    sent_lens, dep_dists = [], []
    for sent in doc.sentences:
        sent_lens.append(len(sent.words))
        for w in sent.words:
            n_words_tagged += 1
            if w.upos:
                pos_c[w.upos] += 1
            feats_str = w.feats or ""
            kv = dict(p.split("=") for p in feats_str.split("|") if "=" in p)
            if "Case" in kv: case_c[kv["Case"]] += 1
            if "Tense" in kv: tense_c[kv["Tense"]] += 1
            if "Aspect" in kv: asp_c[kv["Aspect"]] += 1
            if "Mood" in kv: mood_c[kv["Mood"]] += 1
            if "Gender" in kv: gen_c[kv["Gender"]] += 1
            if w.deprel:
                dep_c[w.deprel.split(":")[0]] += 1
            if w.head and w.head > 0:
                dep_dists.append(abs(w.id - w.head))

    out = dict(feats)
    out["n_sentences"] = n_sents
    out["avg_sentence_length"] = float(np.mean(sent_lens)) if sent_lens else 0.0
    out["dep_distance_mean"] = float(np.mean(dep_dists)) if dep_dists else 0.0
    out["dep_distance_std"] = float(np.std(dep_dists)) if dep_dists else 0.0
    out["case_entropy"] = _entropy(list(case_c.values()))
    out["mood_entropy"] = _entropy(list(mood_c.values()))
    out.update(_safe_prop(pos_c, POS_TAGS, n_words_tagged, "pos_"))
    out.update(_safe_prop(case_c, CASES, sum(case_c.values()), "case_"))
    out.update(_safe_prop(tense_c, TENSES, sum(tense_c.values()), "tense_"))
    out.update(_safe_prop(asp_c, ASPECTS, sum(asp_c.values()), "aspect_"))
    out.update(_safe_prop(mood_c, MOODS, sum(mood_c.values()), "mood_"))
    out.update(_safe_prop(gen_c, GENDERS, sum(gen_c.values()), "gender_"))
    out.update(_safe_prop(dep_c, DEPRELS, sum(dep_c.values()), "dep_rel_"))
    # Derived ratios
    out["noun_verb_ratio"] = (pos_c.get("NOUN", 0) / pos_c["VERB"]) if pos_c.get("VERB") else 0.0
    out["lexical_density"] = (sum(pos_c.get(p, 0) for p in ("NOUN", "VERB", "ADJ", "ADV"))
                              / n_words_tagged) if n_words_tagged else 0.0
    return out


def run(corpus_manifest: Path, out_path: Path, limit: int | None = None) -> Path:
    config.ensure_dirs()
    corpus = pd.read_csv(corpus_manifest)
    if limit:
        corpus = corpus.head(limit)
    rows = []
    for i, row in corpus.iterrows():
        text = Path(row["path"]).read_text(encoding="utf-8", errors="ignore")
        text = normalize_greek(text)  # defensive; idempotent
        if not text.strip():
            continue
        feats = extract_one(text)
        rec = {c: row.get(c) for c in (config.CATEGORY_COLUMNS + config.EXTENDED_ID_COLUMNS)
               if c in corpus.columns}
        rec.update(feats)
        rows.append(rec)
        if (i + 1) % 25 == 0:
            print(f"  extracted {i + 1}/{len(corpus)}")
    df = pd.DataFrame(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Wrote {len(df)} rows x {df.shape[1]} cols -> {out_path}")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", default=str(config.FEATURES_DIR / "features_chunklevel.csv"))
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    run(Path(args.corpus), Path(args.out), args.limit)


if __name__ == "__main__":
    main()
