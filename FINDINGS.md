# Setup findings and decisions

A running log of technical findings made while standing up the study.

## Environment
- Python 3.12.5 (Windows 11). All core packages present in the system interpreter
  (spaCy 3.8.7, textdescriptives 2.8.2, stanza 1.11.1, transformers 5.2.0,
  torch 2.10.0, gensim 4.4.0, statsmodels 0.14.6, sentence-transformers 5.2.3).
- The `myenv12` venv is empty (pip only); the real env is the system Python.
- `torch` is the **CPU build** (`2.10.0+cpu`); GPU needs a CUDA wheel (see env/ENVIRONMENT.md).
- CLTK is **not** installed; the chunk-level extractor therefore uses the installed
  Stanza `grc` PROIEL backend (matches the legacy column scheme).

## Model identifiers (resolved against live APIs)
- GPT-5.5 -> `gpt-5.5` (exact). GPT-4o -> `gpt-4o` (exact).
- Claude 4.8 -> `claude-opus-4-8` (exact).
- Claude 3.5 -> **unavailable**: the Anthropic account now exposes only Claude 4.x
  (`claude-opus-4-8/4-7/4-6/4-5...`, `claude-sonnet-4-*`, `claude-haiku-4-5`).
  Consequence: Claude-3.5 cannot be regenerated on the new chunks; the longitudinal
  Claude point uses the existing legacy Claude-3.5 *documents* (not re-chunked).
  GPT-4o can be regenerated on the same chunks for a clean GPT longitudinal axis.

## Legacy data verification (src/reconcile_legacy.py)
- Three legacy tables: `*_20250321_122021.xlsx` (594x137, keyed by `text_file`),
  `Stylometrics_Ancient_Greek.xlsx` (594x112), `greek_stylo_features.xlsx` (645x131).
- Canonical legacy table rebuilt from the 137-col master: 594 rows; counts by system
  Claude 238 / GPT 237 / Human 119 (Category1 collapses Restricted+Free; the
  Restricted/Free split lives in Category3).
- **Report numbers confirmed**: token length min/max/mean = 275 / 37,106 / 4,294.22,
  exactly matching the prior report's "275 to 37,106 tokens (mean 4,294.22)".

## Corpus chunking
- 119 human docs -> 2,110 chunks at size 250 (median 250 words/chunk).
- Full generation scale (for cost planning): 2,110 chunks x 4 new conditions
  (GPT5/Claude48 x Restricted/Free) = 8,440 calls; +2,110 x 2 for GPT-4o longitudinal.

## Chunk-size calibration (src/calibrate_chunks.py)
- One-shot (no retry) length fidelity with `gpt-5.5`, Restricted prompt.
- See `output/tables/chunk_calibration.csv` and `chosen_size.json` for the result.
- Early signal: at size 150, length ratio ~1.03 and word-overlap Jaccard ~0.74,
  i.e. faithful, length-matched close rewrites.

## End-to-end validation (real data, CPU)
A 103-row mixed smoke set (85 human chunks of `Human_Aeschines_0026001` + 18 AI
rewrites = 3 chunks x {GPT5, Claude48, GPT4o} x {Restricted, Free}) exercised the
whole pipeline successfully:
- Generation length control: every rewrite landed within +/-15% (e.g. GPT5
  150->151/154/146; Claude48 150->150/148/151; GPT4o 150->142/148/150), mostly
  in one attempt.
- Provider fixes: newer models reject some params. `gpt-5.5` rejects `seed`/
  `temperature`; `claude-opus-4-8` rejects `temperature` ("deprecated"). Both
  callers now drop unsupported params and retry. Validated working.
- Extraction (Stanza grc): 103 chunks -> 84 columns in ~36 s (~0.3 s/chunk).
- Embeddings (Ancient-Greek-BERT, CPU): 103 -> WE1..WE50 in ~18 s.
- SOTA stats (`stats_sota.py`): mixed-effects + FDR -> 18 FDR-significant
  Human-vs-AI features; forest plot written.
- Longitudinal (`longitudinal.py`): GPT4o->GPT5 feature-distance-from-human
  delta = -1.21 (negative = GPT-5.5 closer to human style on this sample).
- Legacy engine (`Ancient_Greek_pipeline_lib`, 01-24) via `run_analysis.py`:
  runs through counts/JS/effect-sizes/PCA/author-proximity; on the smoke subset
  it stops only because AI covers a single author (needs >=2 authors). Completes
  on the full 10-author corpus.

## Scale and cost of the full run (to launch explicitly)
- At chosen size 150: 3,518 human chunks. Full 2x2 new models = 4 x 3,518 =
  14,072 generations; + GPT-4o longitudinal (2 x 3,518) = 7,036 -> ~21,000 calls.
- `gpt-5.5` latency observed ~70-90 s/call (reasoning); this dominates wall-clock
  and cost. Budget accordingly; run `generate.py` per-condition (it is idempotent
  and resumable) and consider a larger chunk size (250/400) to cut call count by
  ~40-60% with marginally higher fidelity.
- Extraction of ~21k chunks: ~2-3 h CPU. Embeddings: ~1-2 h CPU (faster on GPU).

## Release
- Private repo: https://github.com/gmikros/ancient-greek-llm-stylometry
- Zenodo DOI to be minted on acceptance (repo made public then).
