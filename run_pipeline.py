"""End-to-end orchestrator for the full-scale run.

Chains: chunk -> generate -> manifest -> extract -> embed -> analyses.
Each step is idempotent/resumable. This is a LONG, API-costly job (see FINDINGS.md
for scale/cost); run intentionally. Use --smoke for a tiny validation pass.

Examples:
    python run_pipeline.py --size 150                      # full run at size 150
    python run_pipeline.py --size 250 --skip-old           # skip GPT-4o longitudinal
    python run_pipeline.py --size 150 --smoke --limit 3    # smoke validation
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable


def sh(args: list[str]) -> None:
    print("\n$", " ".join(args))
    subprocess.run([PY, *args], cwd=ROOT, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=150)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--skip-old", action="store_true", help="skip GPT-4o longitudinal regen")
    args = ap.parse_args()

    systems = ["GPT5", "Claude48"] + ([] if args.skip_old else ["GPT4o"])
    feats = "data/features/features_chunklevel.csv"
    emb = "data/embeddings/greek_document_embeddings.csv"
    corpus = "data/features/corpus_manifest.csv"

    sh(["src/build_chunks.py", "--size", str(args.size)])
    gen = ["src/generate.py", "--systems", *systems, "--prompts", "Restricted", "Free"]
    if args.smoke and args.limit:
        gen += ["--limit", str(args.limit)]
    sh(gen)
    sh(["src/build_corpus_manifest.py", "--size", str(args.size), "--include-legacy-docs"])
    sh(["src/extract_features.py", "--corpus", corpus, "--out", feats] +
       (["--limit", str(args.limit)] if (args.smoke and args.limit) else []))
    sh(["src/embed.py", "--corpus", corpus] +
       (["--limit", str(args.limit)] if (args.smoke and args.limit) else []))
    sh(["src/stats_sota.py", "--features", feats, "--group", "Category4"])
    sh(["src/longitudinal.py", "--features", feats, "--embeddings", emb])
    sh(["src/run_analysis.py", "--features", feats, "--embeddings", emb,
        "--out", "output/analysis"])
    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
