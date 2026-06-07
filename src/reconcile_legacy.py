"""Reconcile the three legacy feature tables and verify reported numbers.

The prior study left three inconsistent feature files. This script documents
their schemas, builds one canonical legacy table (the 137-column master keyed by
text_file, with parsed Category labels), and recomputes a few headline figures
the report cites (sample counts, token-length range, Human-vs-AI effect sizes)
so claims can be checked against the actual data.

Usage:
    python src/reconcile_legacy.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import config  # noqa: E402

PREFIX_TO_LABELS = {  # filename prefix -> (System, Prompt, Label)
    "Human": ("Human", "Human", "Human"),
    "Claude": ("Claude", "Restricted", "AI"), "ClaudeFree": ("Claude", "Free", "AI"),
    "GPT": ("GPT", "Restricted", "AI"), "GPTFree": ("GPT", "Free", "AI"),
}


def _labels_from_text_file(name: str) -> dict:
    stem = Path(str(name)).stem
    prefix = stem.split("_", 1)[0]
    system, prompt, label = PREFIX_TO_LABELS.get(prefix, ("Unknown", "Unknown", "Unknown"))
    parts = stem.split("_")
    author = parts[1] if len(parts) >= 2 else "Unknown"
    return {"Category1": system, "Category2": author, "Category3": prompt, "Category4": label}


def _cohens_d(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return np.nan
    sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return float((a.mean() - b.mean()) / sp) if sp else np.nan


def run() -> None:
    config.ensure_dirs()
    data_dir = Path(config.LEGACY_DATA_DIR)
    report = {"files": {}}
    frames = {}
    for key, fname in config.LEGACY_FEATURE_FILES.items():
        p = data_dir / fname
        if not p.exists():
            report["files"][key] = {"path": str(p), "status": "missing"}
            continue
        df = pd.read_excel(p)
        frames[key] = df
        report["files"][key] = {"path": str(p), "shape": list(df.shape),
                                "has_text_file": "text_file" in df.columns,
                                "category1": sorted(map(str, df["Category1"].unique()))
                                if "Category1" in df.columns else None}

    # Canonical legacy table from the 137-col master (keyed by text_file).
    master = frames.get("master_137")
    if master is not None and "text_file" in master.columns:
        labels = master["text_file"].apply(_labels_from_text_file).apply(pd.Series)
        canonical = pd.concat([labels, master], axis=1)
        out = config.FEATURES_DIR / "legacy_canonical.csv"
        canonical.to_csv(out, index=False, encoding="utf-8")
        report["canonical"] = {"path": str(out), "shape": list(canonical.shape),
                               "counts_by_system": canonical["Category1"].value_counts().to_dict()}

        # Verify a few headline numbers.
        checks = {}
        if "n_tokens" in canonical.columns:
            checks["n_tokens_min"] = float(canonical["n_tokens"].min())
            checks["n_tokens_max"] = float(canonical["n_tokens"].max())
            checks["n_tokens_mean"] = float(canonical["n_tokens"].mean())
        # Human vs AI effect sizes for a few complexity features, if present.
        eff = {}
        for feat in ["L_MTLD", "lexical_density", "case_entropy", "composite_complexity_index"]:
            if feat in canonical.columns:
                a = canonical.loc[canonical["Category4"] == "Human", feat]
                b = canonical.loc[canonical["Category4"] == "AI", feat]
                eff[feat] = _cohens_d(a, b)
        report["verification"] = {"length": checks, "human_vs_ai_cohens_d": eff}

    out_json = config.TABLES_DIR / "legacy_reconciliation.json"
    import json
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nWrote {out_json}")


if __name__ == "__main__":
    run()
