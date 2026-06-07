# Environment

Captured from the working interpreter used for this study.

- OS: Windows 11 (10.0.26200)
- Python: 3.12.5 (CPython, MSC v.1940, 64-bit)
- Full dependency freeze: [`pip-freeze-full.txt`](pip-freeze-full.txt) (270 packages)

## NLP backends used by the pipeline

| Component | Package | Version | Notes |
|---|---|---|---|
| Feature extraction (POS, morphology, dependency, coherence, lexical diversity `L_*`/`td_*`) | `spacy` + `textdescriptives` | 3.8.7 / 2.8.2 | Primary extractor; produces the `pos_*`, `case_*`, `mood_*`, `dep_rel_*`, `td_*`, `L_*` columns |
| Parity / robustness extractor | `stanza` (`grc` PROIEL) | 1.11.1 | Re-extracts identical column names for backend comparison |
| Word embeddings (classic) | `gensim` | 4.4.0 | Word2Vec / FastText used in legacy extractor |
| Document embeddings | `transformers` + `torch` | 5.2.0 / 2.10.0 | HF `pranaydeeps/Ancient-Greek-BERT`, mean-pooled |
| Sentence/doc embeddings (SOTA comparison) | `sentence-transformers` | 5.2.3 | For an additional modern embedding model |
| Statistics | `scipy`, `statsmodels`, `scikit-learn` | 1.16.2 / 0.14.6 / 1.7.2 | Mixed-effects, FDR, classifiers |

## Two environment caveats (action required for full runs)

1. **GPU**: the captured `torch` is the **CPU build** (`2.10.0+cpu`); `torch.cuda.is_available()` is `False` in this interpreter.
   For GPU acceleration (embeddings, perplexity), install a CUDA build matching the local driver, e.g.:
   ```
   pip install --index-url https://download.pytorch.org/whl/cu124 torch==2.10.0
   ```
   The code auto-detects CUDA and falls back to CPU, so it runs either way (slower on CPU).

2. **Ancient Greek spaCy model** is not a PyPI package. Install one of:
   - greCy: `pip install https://huggingface.co/Jacobo/grc_proiel_trf/resolve/main/grc_proiel_trf-any-py3-none-any.whl`
   - odyCy: `pip install https://huggingface.co/chcaa/grc_odycy_joint_trf/resolve/main/grc_odycy_joint_trf-any-py3-none-any.whl`
   Set the chosen model name in `configs/config.py` (`SPACY_GRC_MODEL`).

## API keys

Set as environment variables (or a local `.env`, see `.env.example`):
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

Both were present in the build environment at setup time.
