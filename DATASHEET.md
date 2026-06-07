# Datasheet: Ancient Greek Human vs LLM Rewrite Corpus

Following Gebru et al. (2021), "Datasheets for Datasets."

## Motivation
- **Purpose.** Evaluate how closely modern LLMs reproduce the stylometric and
  linguistic profile of human Ancient Greek (Attic oratory), and whether newer
  models improve over older ones.
- **Created by.** George Mikros (and collaborators), for a submission to
  *Language Resources and Evaluation* (Springer).

## Composition
- **Instances.** Text chunks of Ancient Greek prose, each labeled by:
  System (Human / GPT5 / Claude48 / GPT4o / Claude35), Author (10 orators),
  Prompt (Human / Restricted / Free), Label (Human / AI), plus `doc_id`,
  `chunk_id`, `chunk_index`, `model_version`.
- **Source.** 119 human orator documents (Aeschines, Andocides, Antiphon,
  Demosthenes, Dinarchus, Hyperides, Isaeus, Isocrates, Lycurgus, Lysias),
  segmented into chunks; each human chunk is rewritten by each model x prompt.
- **Human source provenance.** CONFIRMED. All human Greek texts derive from the
  Perseus Digital Library, repository `PerseusDL/canonical-greekLit`
  (Greek TEI editions, `perseus-grc2`), extracted to plaintext and normalized. The
  underlying critical edition per orator (parsed from the TEI `sourceDesc` imprint;
  full table in `output/tables/source_editions.csv` and Appendix B of the paper):
  - Aeschines — Charles Darwin Adams, *The Speeches of Aeschines* (Heinemann, London, 1919).
  - Andocides — K. J. Maidment, *Minor Attic Orators* (Heinemann, London, 1941).
  - Antiphon — K. J. Maidment, *Minor Attic Orators* (Heinemann, London, 1941).
  - Demosthenes — S. H. Butcher (or. 1–26) & W. Rennie (or. 27–61), *Demosthenis Orationes* (Oxford Classical Texts, Clarendon Press, Oxford, 1903–1931).
  - Dinarchus — J. O. Burtt, *Minor Attic Orators* (Heinemann, London, 1954).
  - Hyperides — J. O. Burtt, *Minor Attic Orators* (Heinemann, London, 1954).
  - Isaeus — E. S. Forster, *Isaeus with an English translation* (Harvard Univ. Press, Cambridge MA, 1962).
  - Isocrates — Larue Van Hook, *Isocrates* (Loeb Classical Library; Harvard Univ. Press, Cambridge MA, 1945).
  - Lycurgus — J. O. Burtt, *Minor Attic Orators* (Heinemann, London, 1954).
  - Lysias — W. R. M. Lamb, *Lysias* (Heinemann, London, 1930).
- **Source license.** Nine of the ten Perseus TEI files carry an explicit Creative
  Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) license in their
  `publicationStmt`; the Demosthenes file is an earlier Perseus release (1996) whose
  TEI header states no license ("not stated"). **Share-alike implication:** because
  the corpus is predominantly CC BY-SA, the released human plaintext is a derivative
  work that must be redistributed under a compatible CC BY-SA license (with
  attribution to the Perseus Digital Library and the editions above), and downstream
  reuse inherits the same share-alike obligation.

## Collection process
- Human chunks produced by `src/build_chunks.py` (sentence/word-aligned).
- LLM rewrites produced by `src/generate.py` via the OpenAI and Anthropic APIs,
  with explicit length-matching prompts and retry-on-out-of-tolerance. Every
  call is logged (`output/logs/generation_log.jsonl`): model id, parameters,
  token usage, attempts, and length ratio.
- Chunk size selected by `src/calibrate_chunks.py` (see `output/tables/chosen_size.json`).

## Preprocessing / labeling
- Stylometric features extracted with Stanza `grc` PROIEL (POS, morphology,
  dependency) plus lexical-diversity and entropy metrics (`src/extract_features.py`).
- Document embeddings from `pranaydeeps/Ancient-Greek-BERT` (mean-pooled, PCA-50)
  and a newer SOTA model (`src/embed.py`).

## Uses
- Stylometric/linguistic comparison of human vs LLM Ancient Greek; AI-text
  detection baselines; longitudinal model-progress analysis. Not intended as a
  gold philological edition.

## Distribution & licensing
- Code: MIT. All released data are licensed CC BY-SA 4.0 (Creative Commons
  Attribution-ShareAlike 4.0 International). The human Greek texts derive from the
  Perseus source editions recorded above, which are predominantly CC BY-SA 4.0;
  the ShareAlike obligation therefore propagates to every derivative in this
  release -- the human plaintext chunks, the LLM rewrites generated from them, and
  the per-chunk features and embeddings computed from both. Attribution is owed to
  the Perseus Digital Library and the editions above. Exception/caveat: the
  Demosthenes Perseus file is an earlier release (1996) whose TEI header states no
  license; it is included here with this provenance note. Archived with a Zenodo
  DOI; repository public on acceptance.

## Maintenance
- Maintainer: George Mikros. Versioned via git tags + Zenodo releases.
