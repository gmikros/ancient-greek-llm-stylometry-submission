"""Assemble a labeled corpus manifest spanning all conditions.

Combines:
  - human source chunks (Category1=Human, Category3=Human, Category4=Human)
  - generated chunk rewrites in data/generated/<System><Suffix>/
  - (optional) legacy document-level AI texts for the longitudinal axis

Emits one row per text with: path, Category1..4, doc_id, chunk_id, chunk_index,
author, model_version, text_file. This manifest feeds extract_features.py and
embed.py.

Usage:
    python src/build_corpus_manifest.py --size 250
    python src/build_corpus_manifest.py --size 250 --include-legacy-docs
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import config  # noqa: E402
from src.generate import PROMPT_SUFFIX  # noqa: E402

SUFFIX_TO_PROMPT = {"": "Restricted", "Free": "Free"}
LEGACY_PREFIX_MAP = {  # legacy filename prefix -> (System, Prompt)
    "Human": ("Human", "Human"),
    "Claude": ("Claude35", "Restricted"), "ClaudeFree": ("Claude35", "Free"),
    "GPT": ("GPT4o", "Restricted"), "GPTFree": ("GPT4o", "Free"),
}


def _author_from_doc(doc_id: str) -> str:
    parts = doc_id.split("_")
    return parts[1] if len(parts) >= 2 else "Unknown"


def build(size: int, include_legacy_docs: bool = False) -> Path:
    config.ensure_dirs()
    rows = []

    # 1) Human chunks
    hmanifest = config.CHUNKS_DIR / f"size_{size}" / "chunk_manifest.csv"
    if not hmanifest.exists():
        raise SystemExit(f"Missing {hmanifest}; run build_chunks.py --size {size} first")
    hc = pd.read_csv(hmanifest)
    for _, r in hc.iterrows():
        rows.append({"path": r["chunk_path"], "Category1": "Human", "Category2": r["author"],
                     "Category3": "Human", "Category4": "Human", "doc_id": r["doc_id"],
                     "chunk_id": r["chunk_id"], "chunk_index": r["chunk_index"],
                     "author": r["author"], "model_version": "human",
                     "text_file": Path(r["chunk_path"]).name})

    # 2) Generated chunk rewrites
    for system_key in config.MODELS:
        for prompt_key, suffix in PROMPT_SUFFIX.items():
            d = config.GEN_DIR / f"{system_key}{suffix}"
            if not d.exists():
                continue
            for f in sorted(d.glob("*.txt")):
                # filename: {System}{Suffix}_{doc_id}__c###.txt
                stem = f.stem
                cid = stem.split("_", 1)[1] if "_" in stem else stem
                doc_id = cid.split("__c")[0]
                idx = int(cid.split("__c")[1]) if "__c" in cid else -1
                rows.append({"path": str(f), "Category1": system_key,
                             "Category2": _author_from_doc(doc_id), "Category3": prompt_key,
                             "Category4": "AI", "doc_id": doc_id, "chunk_id": cid,
                             "chunk_index": idx, "author": _author_from_doc(doc_id),
                             "model_version": "new" if system_key in config.NEW_SYSTEMS else "old",
                             "text_file": f.name})

    # 3) Optional legacy document-level AI texts (not chunk-aligned)
    if include_legacy_docs:
        base = Path(config.LEGACY_CORPUS_DIR)
        folder_map = {"Claude": "Claude", "Claude_Free_Corpus": "ClaudeFree",
                      "GPT": "GPT", "GPT_Free_Corpus": "GPTFree"}
        for folder, prefix in folder_map.items():
            d = base / folder
            if not d.exists():
                continue
            system, prompt = LEGACY_PREFIX_MAP[prefix]
            for f in sorted(d.glob("*.txt")):
                doc_id = f.stem
                rows.append({"path": str(f), "Category1": system,
                             "Category2": _author_from_doc(doc_id.replace(prefix + "_", "Human_")),
                             "Category3": prompt, "Category4": "AI", "doc_id": doc_id,
                             "chunk_id": "", "chunk_index": -1,
                             "author": _author_from_doc(doc_id.replace(prefix + "_", "Human_")),
                             "model_version": "legacy_doc", "text_file": f.name})

    df = pd.DataFrame(rows)
    out = config.FEATURES_DIR / "corpus_manifest.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    print(f"Corpus manifest: {len(df)} texts across "
          f"{df['Category1'].nunique()} systems -> {out}")
    print(df.groupby(["Category1", "Category3"]).size().to_string())
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, required=True)
    ap.add_argument("--include-legacy-docs", action="store_true")
    args = ap.parse_args()
    build(args.size, args.include_legacy_docs)


if __name__ == "__main__":
    main()
