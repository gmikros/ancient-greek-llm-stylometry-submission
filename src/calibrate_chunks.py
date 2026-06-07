"""Chunk-size calibration experiment.

The first study's failure mode: LLMs could not reproduce full-document length.
This experiment finds the chunk size that best preserves length while keeping
fidelity high and staying within model output limits.

For each candidate size it: chunks a sample of source docs, rewrites K chunks
with the Restricted prompt (one model), and measures
  - length_ratio = rewritten_words / source_words (target 1.0)
  - in_tolerance rate (within +/- LENGTH_TOLERANCE)
  - mean |length_ratio - 1|
  - fidelity proxy = word-set Jaccard(source, rewrite)  (lexical overlap)
  - failure rate (empty/error)

Picks the SMALLEST size whose in_tolerance rate >= --min-tol-rate, breaking ties
by best fidelity. Writes output/tables/chunk_calibration.csv, chosen_size.json,
and output/figures/chunk_calibration.png.

Usage:
    python src/calibrate_chunks.py                       # defaults (GPT5, Restricted)
    python src/calibrate_chunks.py --model GPT5 --chunks-per-size 8
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import config  # noqa: E402
from src.chunking import split_into_chunks, word_tokens, n_words, parse_human_filename  # noqa: E402
from src.generate import generate_one  # noqa: E402


def _jaccard(a: str, b: str) -> float:
    sa, sb = set(word_tokens(a)), set(word_tokens(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _sample_chunks(size: int, n_docs: int, k: int, rng: np.random.Generator):
    files = sorted(Path(config.SOURCE_HUMAN_DIR).glob("*.txt"))
    if not files:
        raise SystemExit(f"No source texts in {config.SOURCE_HUMAN_DIR}")
    idx = rng.choice(len(files), size=min(n_docs, len(files)), replace=False)
    picked = []
    for i in idx:
        f = files[int(i)]
        meta = parse_human_filename(f)
        chunks = split_into_chunks(f.read_text(encoding="utf-8", errors="ignore"), size)
        for ch in chunks:
            picked.append((meta["doc_id"], ch.text))
    rng.shuffle(picked)
    return picked[:k]


def run(model_key: str, sizes: list[int], n_docs: int, k: int,
        min_tol_rate: float, max_retries: int = 2) -> dict:
    config.ensure_dirs()
    rng = np.random.default_rng(config.RANDOM_SEED)
    rows = []
    for size in sizes:
        sample = _sample_chunks(size, n_docs, k, rng)
        for doc_id, src in sample:
            try:
                res = generate_one(model_key, "Restricted", src, max_retries=max_retries)
                rows.append({"size": size, "doc_id": doc_id,
                             "src_words": res["src_words"], "out_words": res["final_words"],
                             "length_ratio": (res["final_words"] / res["src_words"]) if res["src_words"] else 0.0,
                             "in_tolerance": res["in_tolerance"], "n_attempts": len(res["attempts"]),
                             "fidelity_jaccard": _jaccard(src, res["text"]),
                             "failed": not bool(res["text"])})
            except Exception as e:
                rows.append({"size": size, "doc_id": doc_id, "src_words": n_words(src),
                             "out_words": 0, "length_ratio": 0.0, "in_tolerance": False,
                             "n_attempts": 0, "fidelity_jaccard": 0.0, "failed": True,
                             "error": repr(e)[:200]})
            print(f"  size={size} {doc_id}: ratio={rows[-1]['length_ratio']:.2f} "
                  f"tol={rows[-1]['in_tolerance']} jac={rows[-1]['fidelity_jaccard']:.2f}")

    df = pd.DataFrame(rows)
    out_csv = config.TABLES_DIR / "chunk_calibration_raw.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8")

    agg = (df.groupby("size")
             .agg(n=("size", "size"),
                  tol_rate=("in_tolerance", "mean"),
                  mean_abs_dev=("length_ratio", lambda s: float(np.mean(np.abs(s - 1.0)))),
                  median_ratio=("length_ratio", "median"),
                  fidelity=("fidelity_jaccard", "mean"),
                  mean_attempts=("n_attempts", "mean"),
                  fail_rate=("failed", "mean"))
             .reset_index())
    agg.to_csv(config.TABLES_DIR / "chunk_calibration.csv", index=False, encoding="utf-8")

    eligible = agg[agg["tol_rate"] >= min_tol_rate].sort_values(["size"])
    if len(eligible):
        chosen = int(eligible.iloc[0]["size"])
        reason = f"smallest size with tol_rate>={min_tol_rate}"
    else:
        # fall back to best length parity, then fidelity
        best = agg.sort_values(["mean_abs_dev", "fidelity"], ascending=[True, False]).iloc[0]
        chosen = int(best["size"]); reason = "no size met tol threshold; chose best length parity"

    result = {"chosen_size": chosen, "reason": reason, "min_tol_rate": min_tol_rate,
              "model": config.MODELS[model_key]["model"], "summary": agg.to_dict("records")}
    (config.TABLES_DIR / "chosen_size.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    _plot(agg, chosen)
    print(f"\nCHOSEN chunk size = {chosen} ({reason})")
    return result


def _plot(agg: pd.DataFrame, chosen: int) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(agg["size"], agg["tol_rate"], "o-", label="in-tolerance rate")
        ax.plot(agg["size"], agg["fidelity"], "s-", label="fidelity (Jaccard)")
        ax.plot(agg["size"], agg["mean_abs_dev"], "^-", label="mean |ratio-1|")
        ax.axvline(chosen, ls="--", color="gray", label=f"chosen={chosen}")
        ax.set_xlabel("chunk size (words)"); ax.set_ylabel("metric")
        ax.set_title("Chunk-size calibration"); ax.legend(); ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(config.FIGURES_DIR / "chunk_calibration.png", dpi=200)
        plt.close(fig)
    except Exception as e:  # pragma: no cover
        print(f"  (plot skipped: {e!r})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="GPT5", choices=list(config.MODELS))
    ap.add_argument("--sizes", nargs="+", type=int, default=config.CHUNK_SIZE_CANDIDATES)
    ap.add_argument("--docs", type=int, default=config.CALIBRATION_SAMPLE_DOCS)
    ap.add_argument("--chunks-per-size", type=int, default=config.CALIBRATION_CHUNKS_PER_SIZE)
    ap.add_argument("--min-tol-rate", type=float, default=0.8)
    ap.add_argument("--max-retries", type=int, default=2)
    args = ap.parse_args()
    run(args.model, args.sizes, args.docs, args.chunks_per_size, args.min_tol_rate,
        args.max_retries)


if __name__ == "__main__":
    main()
