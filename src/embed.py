"""Document embeddings for the chunk corpus.

Reproduces the legacy approach (HF `pranaydeeps/Ancient-Greek-BERT`, mean-pooled
last hidden state, truncated to 512 tokens) and reduces to WE1..WE50 via PCA to
match the legacy `greek_document_embeddings.csv` schema. Optionally also embeds
with a newer SOTA Ancient Greek model for comparison.

Outputs:
    data/embeddings/greek_document_embeddings.csv   (WE1..WE50 + Category1-4 + ids)
    data/embeddings/<model>_full.npy                (full-dim matrix)

Usage:
    python src/embed.py --corpus data/features/corpus_manifest.csv
    python src/embed.py --corpus ... --model sota   # use the SOTA comparison model
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import config  # noqa: E402
from src.normalize import normalize_greek  # noqa: E402


def _load(model_name: str):
    import torch
    from transformers import AutoModel, AutoTokenizer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(model_name)
    mdl = AutoModel.from_pretrained(model_name).to(device).eval()
    return tok, mdl, device


def _embed_text(text: str, tok, mdl, device) -> np.ndarray:
    import torch
    inputs = tok(text, return_tensors="pt", truncation=True, padding=True,
                 max_length=512).to(device)
    with torch.no_grad():
        out = mdl(**inputs)
    return out.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()


def run(corpus_manifest: Path, which: str = "agbert",
        reduced_dim: int = config.EMBED_REDUCED_DIM, limit: int | None = None) -> Path:
    config.ensure_dirs()
    model_name = config.AG_BERT_MODEL if which == "agbert" else config.SOTA_EMBED_MODEL
    corpus = pd.read_csv(corpus_manifest)
    if limit:
        corpus = corpus.head(limit)
    tok, mdl, device = _load(model_name)
    print(f"Embedding {len(corpus)} texts with {model_name} on {device}")

    vecs = []
    for i, row in corpus.iterrows():
        text = Path(row["path"]).read_text(encoding="utf-8", errors="ignore")
        text = normalize_greek(text)  # defensive; idempotent
        vecs.append(_embed_text(text, tok, mdl, device))
        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(corpus)}")
    full = np.vstack(vecs)
    np.save(config.EMBEDDINGS_DIR / f"{which}_full.npy", full)

    # PCA -> reduced_dim (WE1..WE50), reproducing the legacy schema.
    from sklearn.decomposition import PCA
    k = min(reduced_dim, full.shape[1], full.shape[0])
    reduced = PCA(n_components=k, random_state=config.RANDOM_SEED).fit_transform(full)

    we_cols = [f"WE{i + 1}" for i in range(k)]
    out = pd.DataFrame(reduced, columns=we_cols)
    for c in config.CATEGORY_COLUMNS + config.EXTENDED_ID_COLUMNS:
        if c in corpus.columns:
            out[c] = corpus[c].values
    out_path = config.EMBEDDINGS_DIR / "greek_document_embeddings.csv"
    out.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Wrote {out.shape} -> {out_path}")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--model", choices=["agbert", "sota"], default="agbert")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    run(Path(args.corpus), "agbert" if args.model == "agbert" else "sota", limit=args.limit)


if __name__ == "__main__":
    main()
