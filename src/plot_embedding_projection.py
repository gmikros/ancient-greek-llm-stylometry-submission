"""Reproduce the Human-vs-AI t-SNE/UMAP composite (Figure 10) with a corrected
draw order.

The original analysis (`Ancient_Greek_embeddings_analysis.py`,
`09_tsne_umap_composite.png`) plots the Human points first and the AI points on
top. Because AI chunks outnumber Human chunks 4:1 (each human chunk is rewritten
by 2 systems x 2 prompts), the dense AI layer visually occludes the human points.
This script recomputes the *same* projection (identical reducers, parameters and
seed) and draws all points in a single **seeded random z-order**, so neither class
systematically occludes the other and the local colour mix reflects the true
~80/20 (AI/Human) class proportion.

Reducers (matching the legacy analysis exactly):
    t-SNE: perplexity=30, max_iter=1000, random_state=42
    UMAP:  n_neighbors=15, min_dist=0.1, random_state=42

Usage:
    python src/plot_embedding_projection.py \
        --embeddings data/embeddings/greek_document_embeddings.csv \
        --out output/analysis/24_Embeddings_Analysis/09_tsne_umap_composite.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from sklearn.manifold import TSNE

DPI = 300
HUMAN_COLOR = "#2ca02c"
AI_COLOR = "#e74c3c"


def _legend_handles():
    return [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=HUMAN_COLOR,
               markersize=8, label="Human"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=AI_COLOR,
               markersize=8, label="AI"),
    ]


def _scatter_shuffled(ax, coords, labels, order):
    """Draw all points in a single seeded random z-order (no class on top)."""
    colors = np.where(labels == "Human", HUMAN_COLOR, AI_COLOR)
    ax.scatter(coords[order, 0], coords[order, 1], c=colors[order],
               s=30, alpha=0.6, edgecolors="none")
    ax.legend(handles=_legend_handles(), loc="best", fontsize=10)


def _scatter_by_author(ax, coords, authors, order):
    """Colour points by author (tab10), single seeded random z-order."""
    auth_order = sorted(np.unique(authors))
    cmap = plt.colormaps["tab10"]
    color_map = {a: cmap(i % 10) for i, a in enumerate(auth_order)}
    cols = np.array([color_map[a] for a in authors])
    ax.scatter(coords[order, 0], coords[order, 1], c=cols[order],
               s=30, alpha=0.6, edgecolors="none")
    handles = [Line2D([0], [0], marker="o", color="w",
                      markerfacecolor=color_map[a], markersize=7, label=a)
               for a in auth_order]
    ax.legend(handles=handles, loc="best", fontsize=8, ncol=2)


def run_three_panel(embeddings_csv: Path, out_png: Path, perplexity: int = 30,
                    random_state: int = 42) -> Path:
    """t-SNE-by-label | UMAP-by-label | UMAP-by-author, sharing one projection."""
    df = pd.read_csv(embeddings_csv)
    we_cols = [c for c in df.columns if c.startswith("WE")]
    X = df[we_cols].values
    labels = df["Category4"].values
    authors = df["Category2"].values
    print(f"Loaded {len(df)} chunks x {len(we_cols)} dims; {df['Category2'].nunique()} authors")

    print("  computing t-SNE...")
    tsne_coords = TSNE(n_components=2, perplexity=perplexity,
                       random_state=random_state, max_iter=1000,
                       verbose=0).fit_transform(X)
    print("  computing UMAP...")
    from umap import UMAP
    umap_coords = UMAP(n_components=2, random_state=random_state,
                       n_neighbors=15, min_dist=0.1).fit_transform(X)

    order = np.random.default_rng(random_state).permutation(len(labels))

    fig, axes = plt.subplots(1, 3, figsize=(22, 6.5))
    _scatter_shuffled(axes[0], tsne_coords, labels, order)
    axes[0].set_xlabel("t-SNE 1", fontsize=11)
    axes[0].set_ylabel("t-SNE 2", fontsize=11)
    axes[0].set_title("(A) t-SNE \u2014 Human vs AI", fontsize=12)
    axes[0].grid(True, alpha=0.3)

    _scatter_shuffled(axes[1], umap_coords, labels, order)
    axes[1].set_xlabel("UMAP 1", fontsize=11)
    axes[1].set_ylabel("UMAP 2", fontsize=11)
    axes[1].set_title("(B) UMAP \u2014 Human vs AI", fontsize=12)
    axes[1].grid(True, alpha=0.3)

    _scatter_by_author(axes[2], umap_coords, authors, order)
    axes[2].set_xlabel("UMAP 1", fontsize=11)
    axes[2].set_ylabel("UMAP 2", fontsize=11)
    axes[2].set_title("(C) UMAP \u2014 by author", fontsize=12)
    axes[2].grid(True, alpha=0.3)

    plt.suptitle("Embedding Space: Human vs AI is secondary to author/content structure",
                 fontsize=14)
    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out_png}")
    return out_png


def run(embeddings_csv: Path, out_png: Path, perplexity: int = 30,
        random_state: int = 42) -> Path:
    df = pd.read_csv(embeddings_csv)
    we_cols = [c for c in df.columns if c.startswith("WE")]
    X = df[we_cols].values
    labels = df["Category4"].values
    n_human = int((labels == "Human").sum())
    n_ai = int((labels == "AI").sum())
    print(f"Loaded {len(df)} chunks ({n_human} Human, {n_ai} AI) x {len(we_cols)} dims")

    print("  computing t-SNE...")
    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=random_state,
                max_iter=1000, verbose=0)
    tsne_coords = tsne.fit_transform(X)

    print("  computing UMAP...")
    from umap import UMAP
    umap = UMAP(n_components=2, random_state=random_state, n_neighbors=15,
                min_dist=0.1)
    umap_coords = umap.fit_transform(X)

    # Single seeded permutation shared by both panels for reproducible z-order.
    order = np.random.default_rng(random_state).permutation(len(labels))

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    _scatter_shuffled(axes[0], tsne_coords, labels, order)
    axes[0].set_xlabel("t-SNE 1", fontsize=11)
    axes[0].set_ylabel("t-SNE 2", fontsize=11)
    axes[0].set_title("(A) t-SNE Projection", fontsize=12)
    axes[0].grid(True, alpha=0.3)

    _scatter_shuffled(axes[1], umap_coords, labels, order)
    axes[1].set_xlabel("UMAP 1", fontsize=11)
    axes[1].set_ylabel("UMAP 2", fontsize=11)
    axes[1].set_title("(B) UMAP Projection", fontsize=12)
    axes[1].grid(True, alpha=0.3)

    plt.suptitle("Embedding Space Visualization: Human vs AI", fontsize=14)
    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out_png}")
    return out_png


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--embeddings", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["composite", "three"], default="composite")
    ap.add_argument("--perplexity", type=int, default=30)
    ap.add_argument("--random-state", type=int, default=42)
    args = ap.parse_args()
    fn = run_three_panel if args.mode == "three" else run
    fn(Path(args.embeddings), Path(args.out), args.perplexity, args.random_state)


if __name__ == "__main__":
    main()
