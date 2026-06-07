# Ancient Greek LLM Stylometry: a Resource and Evaluation

[![Code License: MIT](https://img.shields.io/badge/Code%20License-MIT-blue.svg)](LICENSE)
[![Data License: CC BY-SA 4.0](https://img.shields.io/badge/Data%20License-CC%20BY--SA%204.0-lightgrey.svg)](DATASHEET.md)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](env/ENVIRONMENT.md)
[![NLP: Stanza grc PROIEL](https://img.shields.io/badge/NLP-Stanza%20grc%20PROIEL-orange)](https://stanfordnlp.github.io/stanza/)
[![Embeddings: Ancient-Greek-BERT](https://img.shields.io/badge/Embeddings-Ancient--Greek--BERT-yellow)](https://huggingface.co/pranaydeeps/Ancient-Greek-BERT)
[![Venue: LRE (Springer)](https://img.shields.io/badge/Venue-Language%20Resources%20%26%20Evaluation-9cf)](https://www.springer.com/journal/10579)
[![DOI: pending](https://img.shields.io/badge/DOI-pending%20(Zenodo)-red.svg)](#citation)

How closely do state-of-the-art LLMs (GPT-5.5, Claude 4.8) write Ancient Greek
compared to the human Attic orators, and have they improved over the previous
generation (GPT-4o, Claude 3.5)? This repository contains the corpus, code, and
analyses for a chunk-level stylometric and linguistic evaluation, prepared as a
language resource for *Language Resources and Evaluation* (Springer).

> **Submission artifact repository.** This repository accompanies the journal
> submission and contains the corpus, code, and all analysis artifacts. The
> manuscript itself is intentionally **not** included here. Two oversized,
> regenerable intermediates (the 6610x6610 `embedding_distance_matrix.npy` files,
> ~333 MB each) are omitted to stay within GitHub limits; they are recreated by
> re-running the embedding analysis.

## What is here

```
configs/        central config (paths, model ids, design, chunking)
prompts/        versioned Restricted (close-rewrite) + Free prompts
src/            pipeline modules (chunking, generation, extraction, embeddings,
                analysis, SOTA stats, longitudinal comparison, reconciliation)
data/           chunks, generated rewrites, features, embeddings
output/         logs, tables, figures, analysis outputs (01-24)
env/            pinned requirements + environment notes
DATASHEET.md    datasheet-for-datasets describing the released corpus
```

## Design

- Source: 119 human Attic-orator texts (10 authors).
- Unit of analysis: **chunk** (sentence/word-aligned), so models can reproduce
  length faithfully. The chunk size is chosen by a calibration experiment
  (`src/calibrate_chunks.py`).
- Conditions: 2 prompts (Restricted = rewrite as close as possible incl. length;
  Free = meaning-preserving but flexible) x {GPT-5.5, Claude-4.8}, plus the older
  GPT-4o (regenerated on the same chunks) and the legacy Claude-3.5 documents for
  the longitudinal axis.
- Category schema (matches the analysis engine): `Category1`=System,
  `Category2`=Author, `Category3`=Prompt, `Category4`=Label, extended with
  `doc_id`, `chunk_id`, `chunk_index`, `model_version`, `text_file`.

## Reproduce

```bash
# 0. Environment (Python 3.12). See env/ENVIRONMENT.md for the AG spaCy model + GPU torch.
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY, ANTHROPIC_API_KEY

# 1. Resolve model ids against the live APIs
python src/probe_models.py

# 2. Calibrate chunk size (length-preservation experiment)
python src/calibrate_chunks.py --model GPT5

# 3. Chunk the corpus at the chosen size and build the corpus manifest
python src/build_chunks.py --size <chosen>
python src/build_corpus_manifest.py --size <chosen> --include-legacy-docs

# 4. Generate rewrites (full 2x2 + GPT-4o longitudinal)
python src/generate.py --systems GPT5 Claude48 GPT4o --prompts Restricted Free

# 5. Features + embeddings (chunk level)
python src/build_corpus_manifest.py --size <chosen> --include-legacy-docs
python src/extract_features.py --corpus data/features/corpus_manifest.csv
python src/embed.py --corpus data/features/corpus_manifest.csv

# 6. Analyses (proven engine 01-24 + SOTA stats + longitudinal)
python src/run_analysis.py --features data/features/features_chunklevel.csv \
    --embeddings data/embeddings/greek_document_embeddings.csv
python src/stats_sota.py --features data/features/features_chunklevel.csv --group Category4
python src/longitudinal.py --features data/features/features_chunklevel.csv \
    --embeddings data/embeddings/greek_document_embeddings.csv

# (validation of the prior study's numbers)
python src/reconcile_legacy.py
```

## Notes / caveats

- The analysis engine (`Ancient_Greek_pipeline_lib.py`, analyses 01-24) is reused
  from the authors' prior work; `src/run_analysis.py` wraps it with this project's
  column schema.
- The installed `torch` is a CPU build; install a CUDA build for GPU acceleration
  (embeddings/perplexity). The code auto-detects and falls back to CPU.
- Claude-3.5 is no longer served by the Anthropic API used here, so the legacy
  Claude-3.5 *documents* (not re-chunked) anchor the Claude longitudinal point.

## Citation

If you use this corpus, code, or analyses, please cite the resource. Machine-readable
metadata is in [`CITATION.cff`](CITATION.cff); a DOI will be minted via Zenodo on the
tagged release at acceptance.

```bibtex
@misc{mikros_ag_llm_stylometry,
  author       = {Mikros, George},
  title        = {Ancient Greek LLM Stylometry: a Resource and Evaluation
                  of Human vs.\ LLM-generated Attic Prose},
  year         = {2026},
  howpublished = {\url{https://github.com/gmikros/ancient-greek-llm-stylometry-submission}},
  note         = {Code: MIT; Data: CC BY-SA 4.0. DOI pending (Zenodo).}
}
```

Please also credit the underlying source editions of the [Perseus Digital
Library](http://www.perseus.tufts.edu/) (see `DATASHEET.md` and
`output/tables/source_editions.csv`).

## License

Code: MIT (`LICENSE`). Data/corpus: CC BY-SA 4.0 (see `DATASHEET.md`). The human
Greek texts derive from the Perseus Digital Library editions (predominantly
CC BY-SA 4.0), so the released data inherit the ShareAlike term; downstream reuse
carries the same obligation, with attribution to Perseus and the source editions.
