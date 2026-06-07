"""Chunk the human orator corpus into sentence/word-aligned chunks.

Writes one .txt per chunk under data/chunks/size_<N>/ and a manifest CSV that
generate.py and the extractor consume.

Usage:
    python src/build_chunks.py --size 250
    python src/build_chunks.py --size 250 --docs Human_Lysias_0540001 Human_Lysias_0540014
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import config  # noqa: E402
from src.chunking import split_into_chunks, parse_human_filename, chunk_record, n_words  # noqa: E402
from src.normalize import normalize_greek  # noqa: E402


def build(size: int, docs: list[str] | None = None) -> Path:
    config.ensure_dirs()
    out_root = config.CHUNKS_DIR / f"size_{size}"
    out_root.mkdir(parents=True, exist_ok=True)

    src_files = sorted(Path(config.SOURCE_HUMAN_DIR).glob("*.txt"))
    if docs:
        wanted = set(docs)
        src_files = [f for f in src_files if f.stem in wanted]
    if not src_files:
        raise SystemExit(f"No source texts found in {config.SOURCE_HUMAN_DIR}")

    records = []
    for f in src_files:
        meta = parse_human_filename(f)
        text = f.read_text(encoding="utf-8", errors="ignore")
        chunks = split_into_chunks(text, target_words=size)
        for ch in chunks:
            # Normalize to the source-corpus convention (lowercase, keep
            # diacritics, drop punctuation/apostrophes) before writing and
            # before n_words is recorded in the manifest.
            ch.text = normalize_greek(ch.text)
            ch.n_words = n_words(ch.text)
            rec = chunk_record(meta["doc_id"], meta["author"], ch, size)
            chunk_path = out_root / f"{rec['chunk_id']}.txt"
            chunk_path.write_text(ch.text, encoding="utf-8")
            rec["chunk_path"] = str(chunk_path)
            records.append(rec)

    df = pd.DataFrame(records)
    manifest = out_root / "chunk_manifest.csv"
    df.to_csv(manifest, index=False, encoding="utf-8")
    # Also expose the latest manifest at the default location used by generate.py.
    df.to_csv(config.CHUNKS_DIR / "chunk_manifest.csv", index=False, encoding="utf-8")

    print(f"size={size}: {len(src_files)} docs -> {len(df)} chunks "
          f"(median {int(df['n_words'].median())} words/chunk). Manifest: {manifest}")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, required=True)
    ap.add_argument("--docs", nargs="*", default=None)
    args = ap.parse_args()
    build(args.size, args.docs)


if __name__ == "__main__":
    main()
