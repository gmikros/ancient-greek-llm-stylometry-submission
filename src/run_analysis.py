"""Run the proven analysis engine on the new chunk-level feature table.

Wraps the existing `Ancient_Greek_pipeline_lib` (analyses 01-23) and
`Ancient_Greek_embeddings_analysis` (analysis 24) by adding the pipeline code
directory to sys.path and passing our column schema via meta_override.

Usage:
    python src/run_analysis.py --features data/features/features_chunklevel.csv \
        --embeddings data/embeddings/greek_document_embeddings.csv \
        --out output/analysis
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# The legacy library prints Unicode arrows; force UTF-8 stdout on Windows consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import config  # noqa: E402


def _import_pipeline():
    sys.path.insert(0, str(Path(config.PIPELINE_CODE_DIR)))
    import importlib
    lib = importlib.import_module("Ancient_Greek_pipeline_lib")
    try:
        emb = importlib.import_module("Ancient_Greek_embeddings_analysis")
    except Exception:
        emb = None
    return lib, emb


def run(features: Path, out_base: Path, embeddings: Path | None) -> None:
    out_base.mkdir(parents=True, exist_ok=True)
    lib, emb = _import_pipeline()

    # The legacy pipeline reads an Excel file and auto-detects the Category1-4
    # metadata columns, so convert CSV -> xlsx and rely on auto-detection.
    feats_path = features
    if features.suffix.lower() == ".csv":
        import pandas as pd
        xlsx = features.with_suffix(".xlsx")
        pd.read_csv(features).to_excel(xlsx, index=False)
        feats_path = xlsx

    print(f"Running full pipeline (01-23) on {feats_path}")
    lib.run_full_pipeline(data_path=str(feats_path), output_base=str(out_base))

    if embeddings and emb is not None:
        print("Running embedding analysis (24)")
        emb.run_embedding_analysis(str(embeddings), str(feats_path), str(out_base))
    elif embeddings:
        print("Embedding analysis module not importable; skipped.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--embeddings", default=None)
    ap.add_argument("--out", default=str(config.OUTPUT_DIR / "analysis"))
    args = ap.parse_args()
    run(Path(args.features), Path(args.out),
        Path(args.embeddings) if args.embeddings else None)


if __name__ == "__main__":
    main()
