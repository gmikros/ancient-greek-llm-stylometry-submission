"""Longitudinal comparison: old (GPT-4o / Claude-3.5) vs new (GPT-5.5 / Claude-4.8).

Quantifies whether the newer models are measurably closer to human Ancient Greek
style, using (a) standardized distance of each system's centroid from the human
centroid in feature space, (b) per-feature effect sizes old vs new, and
(c) embedding distance from the human centroid.

Usage:
    python src/longitudinal.py --features data/features/features_chunklevel.csv \
        --embeddings data/embeddings/greek_document_embeddings.csv --out output/tables
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import config  # noqa: E402

NON_FEATURE = set(config.CATEGORY_COLUMNS + config.EXTENDED_ID_COLUMNS + ["author", "path"])
PAIRS = [("GPT4o", "GPT5"), ("Claude35", "Claude48")]


def _feature_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in NON_FEATURE
            and pd.api.types.is_numeric_dtype(df[c])]


def _centroid_distance(df: pd.DataFrame, feats: list[str]) -> pd.DataFrame:
    """Standardized Euclidean distance of each system centroid from Human."""
    from sklearn.preprocessing import StandardScaler
    X = StandardScaler().fit_transform(df[feats].fillna(df[feats].mean()))
    Z = pd.DataFrame(X, columns=feats)
    Z["system"] = df["Category1"].values
    human = Z[Z["system"] == "Human"][feats].mean().values
    out = []
    for sysname, g in Z.groupby("system"):
        if sysname == "Human":
            continue
        c = g[feats].mean().values
        out.append({"system": sysname, "feature_distance_from_human": float(np.linalg.norm(c - human)),
                    "n": len(g)})
    return pd.DataFrame(out)


def _embedding_distance(emb_path: Path) -> pd.DataFrame:
    from scipy.spatial.distance import cosine
    e = pd.read_csv(emb_path)
    we = [c for c in e.columns if c.startswith("WE")]
    human = e[e["Category1"] == "Human"][we].mean().values
    out = []
    for sysname, g in e.groupby("Category1"):
        if sysname == "Human":
            continue
        dists = [cosine(row, human) for row in g[we].values]
        out.append({"system": sysname, "embed_cosine_from_human": float(np.mean(dists)), "n": len(g)})
    return pd.DataFrame(out)


def run(features: Path, out_dir: Path, embeddings: Path | None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(features)
    feats = _feature_cols(df)
    fd = _centroid_distance(df, feats)
    summary = fd
    if embeddings and Path(embeddings).exists():
        ed = _embedding_distance(Path(embeddings))
        summary = fd.merge(ed, on="system", how="outer")

    # Improvement deltas per family (negative = new closer to human).
    deltas = []
    for old, new in PAIRS:
        row = {"pair": f"{old}->{new}"}
        for col in ("feature_distance_from_human", "embed_cosine_from_human"):
            if col in summary.columns:
                ov = summary.loc[summary["system"] == old, col]
                nv = summary.loc[summary["system"] == new, col]
                if len(ov) and len(nv):
                    row[f"delta_{col}"] = float(nv.values[0] - ov.values[0])
        deltas.append(row)
    deltas = pd.DataFrame(deltas)

    summary.to_csv(out_dir / "longitudinal_distances.csv", index=False, encoding="utf-8")
    deltas.to_csv(out_dir / "longitudinal_deltas.csv", index=False, encoding="utf-8")
    _plot(summary, out_dir / "longitudinal_distance_from_human.png")
    print("Longitudinal summary:\n", summary.to_string(index=False))
    print("\nDeltas (new - old; negative = improved):\n", deltas.to_string(index=False))
    return out_dir / "longitudinal_distances.csv"


def _plot(summary: pd.DataFrame, out_png: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        s = summary.sort_values("feature_distance_from_human")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(s["system"], s["feature_distance_from_human"])
        ax.set_ylabel("standardized feature distance from human centroid")
        ax.set_title("Distance from human style by system (lower = closer)")
        ax.tick_params(axis="x", rotation=30)
        fig.tight_layout(); fig.savefig(out_png, dpi=200); plt.close(fig)
    except Exception as e:  # pragma: no cover
        print(f"  (plot skipped: {e!r})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--embeddings", default=None)
    ap.add_argument("--out", default=str(config.TABLES_DIR))
    args = ap.parse_args()
    run(Path(args.features), Path(args.out),
        Path(args.embeddings) if args.embeddings else None)


if __name__ == "__main__":
    main()
