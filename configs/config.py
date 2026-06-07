"""Central configuration for the Ancient Greek LLM Stylometry (LREC) study.

All paths resolve relative to the repository root so the project can be moved
freely. External inputs (the existing corpus, legacy feature tables, and the
proven analysis library) are referenced read-only via absolute paths that can
be overridden with environment variables.
"""
from __future__ import annotations

import os
from pathlib import Path

# --- Repository layout -----------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
PROMPTS_DIR = REPO_ROOT / "prompts"
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "output"

# Generated/derived data subfolders (created on demand).
CHUNKS_DIR = DATA_DIR / "chunks"                 # human source chunks
GEN_DIR = DATA_DIR / "generated"                 # LLM rewrites (by condition)
FEATURES_DIR = DATA_DIR / "features"             # extracted feature tables
EMBEDDINGS_DIR = DATA_DIR / "embeddings"         # document embeddings
LOGS_DIR = OUTPUT_DIR / "logs"
FIGURES_DIR = OUTPUT_DIR / "figures"
TABLES_DIR = OUTPUT_DIR / "tables"


def _env_path(var: str, default: str) -> Path:
    return Path(os.environ.get(var, default))


# --- External inputs (read-only) -------------------------------------------
# The existing human orator corpus (119 texts) lives in the surrounding project.
PROJECT_ROOT = REPO_ROOT.parent  # ...\Paroysiaseis\Cyprus 2025
SOURCE_HUMAN_DIR = _env_path(
    "AG_SOURCE_HUMAN_DIR",
    str(PROJECT_ROOT / "Texts" / "Ancient Greek Corpus" / "Human"),
)
# Existing (older-model) AI rewrites, used for the longitudinal axis.
LEGACY_CORPUS_DIR = _env_path(
    "AG_LEGACY_CORPUS_DIR",
    str(PROJECT_ROOT / "Texts" / "Ancient Greek Corpus"),
)
# Directory holding the proven analysis library + embeddings analysis.
PIPELINE_CODE_DIR = _env_path(
    "AG_PIPELINE_CODE_DIR",
    r"C:\Users\USER01\Dropbox\Workplace\D\George\PAPERS\Code\Python",
)
# Legacy feature tables to reconcile/verify against.
LEGACY_DATA_DIR = _env_path(
    "AG_LEGACY_DATA_DIR",
    str(PROJECT_ROOT / "Data"),
)
LEGACY_FEATURE_FILES = {
    "master_137": "Stylometrics_Ancient_Greek_20250321_122021.xlsx",
    "labeled_112": "Stylometrics_Ancient_Greek.xlsx",
    "features_131": "greek_stylo_features.xlsx",
}

# --- Models ----------------------------------------------------------------
# API model identifiers. Resolve/validate with: python src/probe_models.py
# Defaults are the latest-generation aliases requested for this study; the probe
# script writes the concrete resolved ids to configs/resolved_models.json.
MODELS = {
    "GPT5":     {"provider": "openai",    "model": os.environ.get("AG_GPT5_MODEL", "gpt-5.5")},
    "Claude48": {"provider": "anthropic", "model": os.environ.get("AG_CLAUDE48_MODEL", "claude-opus-4-8")},
    # Older generation, for the longitudinal comparison (regenerate on same chunks).
    "GPT4o":    {"provider": "openai",    "model": os.environ.get("AG_GPT4O_MODEL", "gpt-4o")},
    "Claude35": {"provider": "anthropic", "model": os.environ.get("AG_CLAUDE35_MODEL", "claude-3-5-sonnet-latest")},
}
NEW_SYSTEMS = ["GPT5", "Claude48"]
OLD_SYSTEMS = ["GPT4o", "Claude35"]

# Generation decoding parameters (logged with every call).
GEN_PARAMS = {
    "temperature": 0.7,
    "max_output_tokens": 4096,
    "seed": 7,  # OpenAI honors seed; logged for reproducibility regardless.
}

# Document embedding models.
AG_BERT_MODEL = "pranaydeeps/Ancient-Greek-BERT"   # legacy / primary
SOTA_EMBED_MODEL = os.environ.get(
    "AG_SOTA_EMBED_MODEL", "bowphs/GreBerta"          # newer AG model for comparison
)
EMBED_REDUCED_DIM = 50  # reproduce the legacy WE1..WE50 reduction (PCA)

# Perplexity / fluency LM (Greek-capable).
PERPLEXITY_MODEL = os.environ.get("AG_PPL_MODEL", "pranaydeeps/Ancient-Greek-BERT")

# Ancient Greek spaCy model (install separately; see env/ENVIRONMENT.md).
SPACY_GRC_MODEL = os.environ.get("AG_SPACY_GRC_MODEL", "grc_proiel_trf")
STANZA_LANG = "grc"
STANZA_PACKAGE = "proiel"

# --- Experimental design ----------------------------------------------------
PROMPTS = {"Restricted": PROMPTS_DIR / "restricted.txt",
           "Free": PROMPTS_DIR / "free.txt"}

# Category schema (matches the existing pipeline; extended with version/ids).
# Category1 = System, Category2 = Author, Category3 = Prompt, Category4 = Label
CATEGORY_COLUMNS = ["Category1", "Category2", "Category3", "Category4"]
EXTENDED_ID_COLUMNS = ["doc_id", "chunk_id", "chunk_index", "model_version", "text_file"]

# Authors (10 orators), used for filename parsing + grouping.
AUTHORS = ["Aeschines", "Andocides", "Antiphon", "Demosthenes", "Dinarchus",
           "Hyperides", "Isaeus", "Isocrates", "Lycurgus", "Lysias"]

# --- Chunking calibration ---------------------------------------------------
# Candidate chunk sizes (in word-like tokens), sentence-aligned boundaries.
CHUNK_SIZE_CANDIDATES = [100, 150, 250, 400]
LENGTH_TOLERANCE = 0.15          # accept rewrites within +/-15% of source length
CALIBRATION_SAMPLE_DOCS = 6      # docs sampled for the calibration experiment
CALIBRATION_CHUNKS_PER_SIZE = 8  # chunks rewritten per size during calibration
RANDOM_SEED = 42

# --- Statistics -------------------------------------------------------------
FDR_ALPHA = 0.05
BOOTSTRAP_N = 5000


def ensure_dirs() -> None:
    for d in (DATA_DIR, OUTPUT_DIR, CHUNKS_DIR, GEN_DIR, FEATURES_DIR,
              EMBEDDINGS_DIR, LOGS_DIR, FIGURES_DIR, TABLES_DIR):
        d.mkdir(parents=True, exist_ok=True)
