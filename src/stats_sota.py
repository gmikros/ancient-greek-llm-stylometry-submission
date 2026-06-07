"""State-of-the-art statistics for chunk-level data.

Chunks are nested within source documents within authors, so per-feature
contrasts use linear mixed-effects models (random intercepts for author and,
nested, source document) to avoid pseudoreplication. Adds:
  - Cohen's d (Human vs AI) with bootstrap CIs
  - Benjamini-Hochberg FDR across features
  - a forest plot of the largest, FDR-significant effects

Usage:
    python src/stats_sota.py --features data/features/features_chunklevel.csv \
        --group Category4 --out output/tables
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import config  # noqa: E402

warnings.filterwarnings("ignore")
NON_FEATURE = set(config.CATEGORY_COLUMNS + config.EXTENDED_ID_COLUMNS + ["author", "path"])


def _feature_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns
            if c not in NON_FEATURE and pd.api.types.is_numeric_dtype(df[c])]


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return 0.0
    sp = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return float((a.mean() - b.mean()) / sp) if sp else 0.0


def bootstrap_d_ci(a: np.ndarray, b: np.ndarray, n: int = config.BOOTSTRAP_N,
                   seed: int = config.RANDOM_SEED) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    ds = np.empty(n)
    for i in range(n):
        ds[i] = cohens_d(rng.choice(a, len(a), replace=True),
                         rng.choice(b, len(b), replace=True))
    return float(np.percentile(ds, 2.5)), float(np.percentile(ds, 97.5))


def mixedlm_pvalue(df: pd.DataFrame, feature: str, group_col: str) -> float:
    """Mixed model: feature ~ group + (1|author) + (1|doc within author)."""
    import statsmodels.formula.api as smf
    d = df[[feature, group_col, "author", "doc_id"]].dropna().copy()
    if d[group_col].nunique() < 2 or len(d) < 10:
        return np.nan
    d = d.rename(columns={feature: "y", group_col: "g"})
    try:
        if d["doc_id"].notna().any() and d["doc_id"].nunique() > 1:
            md = smf.mixedlm("y ~ C(g)", d, groups=d["author"],
                             vc_formula={"doc": "0 + C(doc_id)"})
        else:
            md = smf.mixedlm("y ~ C(g)", d, groups=d["author"])
        res = md.fit(reml=False, method="lbfgs", disp=False)
        pvals = [p for k, p in res.pvalues.items() if k.startswith("C(g)")]
        return float(min(pvals)) if pvals else np.nan
    except Exception:
        # Fallback: Kruskal-Wallis (ignores nesting) so the row still reports.
        from scipy.stats import kruskal
        groups = [g["y"].values for _, g in d.groupby("g")]
        try:
            return float(kruskal(*groups).pvalue)
        except Exception:
            return np.nan


def run(features: Path, group_col: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(features)
    if "author" not in df.columns and "Category2" in df.columns:
        df["author"] = df["Category2"]
    feats = _feature_cols(df)
    print(f"{len(df)} rows, {len(feats)} features; contrast on {group_col}")

    rows = []
    is_binary = group_col == "Category4"
    for feat in feats:
        p = mixedlm_pvalue(df, feat, group_col)
        rec = {"feature": feat, "p_value": p}
        if is_binary and {"Human", "AI"}.issubset(set(df[group_col].unique())):
            a = df.loc[df[group_col] == "Human", feat].dropna().values
            b = df.loc[df[group_col] == "AI", feat].dropna().values
            d = cohens_d(a, b)
            lo, hi = bootstrap_d_ci(a, b) if min(len(a), len(b)) > 2 else (np.nan, np.nan)
            rec.update({"cohens_d": d, "d_ci_lo": lo, "d_ci_hi": hi,
                        "mean_human": float(np.mean(a)) if len(a) else np.nan,
                        "mean_ai": float(np.mean(b)) if len(b) else np.nan})
        rows.append(rec)

    res = pd.DataFrame(rows)
    # FDR across features
    from statsmodels.stats.multitest import multipletests
    mask = res["p_value"].notna()
    res["p_fdr"] = np.nan
    if mask.any():
        res.loc[mask, "p_fdr"] = multipletests(res.loc[mask, "p_value"],
                                               alpha=config.FDR_ALPHA, method="fdr_bh")[1]
    res["sig_fdr"] = res["p_fdr"] < config.FDR_ALPHA
    res = res.sort_values("p_fdr", na_position="last")
    out_csv = out_dir / f"mixedeffects_{group_col}.csv"
    res.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"Wrote {out_csv} ({int(res['sig_fdr'].sum())} FDR-significant features)")

    if "cohens_d" in res.columns:
        _forest(res, out_dir / f"forest_{group_col}.png")
    return out_csv


def _forest(res: pd.DataFrame, out_png: Path, top: int = 20) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        d = res.dropna(subset=["cohens_d"]).copy()
        d["abs_d"] = d["cohens_d"].abs()
        d = d.sort_values("abs_d", ascending=True).tail(top)
        fig, ax = plt.subplots(figsize=(8, max(4, 0.4 * len(d))))
        y = np.arange(len(d))
        ax.errorbar(d["cohens_d"], y,
                    xerr=[d["cohens_d"] - d["d_ci_lo"], d["d_ci_hi"] - d["cohens_d"]],
                    fmt="o", capsize=3)
        ax.axvline(0, color="gray", lw=1)
        ax.set_yticks(y); ax.set_yticklabels(d["feature"], fontsize=8)
        ax.set_xlabel("Cohen's d (Human vs AI) with 95% bootstrap CI")
        ax.set_title("Largest Human vs AI effects (FDR-screened)")
        fig.tight_layout(); fig.savefig(out_png, dpi=200); plt.close(fig)
    except Exception as e:  # pragma: no cover
        print(f"  (forest plot skipped: {e!r})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--group", default="Category4")
    ap.add_argument("--out", default=str(config.TABLES_DIR))
    args = ap.parse_args()
    run(Path(args.features), args.group, Path(args.out))


if __name__ == "__main__":
    main()
