"""Ancient Greek text chunking utilities.

The orator source texts are largely unpunctuated continuous prose, so the
default strategy is greedy word-window chunking with optional sentence-aware
boundaries when terminal punctuation is present. Token counting uses a
Greek-aware word regex shared across the project for consistency.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

# Greek letters incl. polytonic diacritics; keep intra-word apostrophe/elision.
_WORD_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]+(?:['\u2019\u02BC][\u0370-\u03FF\u1F00-\u1FFF]+)*")
# Terminal punctuation in (punctuated) Greek: '.', ';' (Greek question mark is ';'), '·' (ano teleia).
_SENT_SPLIT_RE = re.compile(r"(?<=[\.;\u00B7\u037E])\s+")


def word_tokens(text: str) -> List[str]:
    """Return Greek word-like tokens (the project-wide length unit)."""
    return _WORD_RE.findall(text)


def n_words(text: str) -> int:
    return len(word_tokens(text))


def _sentences(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    parts = _SENT_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


@dataclass
class Chunk:
    chunk_index: int
    text: str
    n_words: int


def split_into_chunks(text: str, target_words: int,
                      sentence_aware: bool = True) -> List[Chunk]:
    """Split text into chunks of ~target_words.

    If sentence_aware and the text contains terminal punctuation, accumulate
    whole sentences until the target is reached. Otherwise fall back to pure
    word-window chunking. A trailing chunk shorter than half the target is
    merged into the previous chunk to avoid tiny remainders.
    """
    sents = _sentences(text) if sentence_aware else []
    use_sentences = len(sents) > 1

    chunks: List[List[str]] = []
    if use_sentences:
        cur: List[str] = []
        cur_n = 0
        for s in sents:
            sn = n_words(s)
            if cur and cur_n + sn > target_words:
                chunks.append(cur)
                cur, cur_n = [], 0
            cur.append(s)
            cur_n += sn
        if cur:
            chunks.append(cur)
        texts = [" ".join(c) for c in chunks]
    else:
        toks = word_tokens(text)
        texts = [" ".join(toks[i:i + target_words])
                 for i in range(0, len(toks), target_words)]

    # Merge a tiny trailing remainder into the previous chunk.
    if len(texts) >= 2 and n_words(texts[-1]) < target_words / 2:
        texts[-2] = texts[-2] + " " + texts[-1]
        texts.pop()

    return [Chunk(chunk_index=i, text=t, n_words=n_words(t))
            for i, t in enumerate(texts)]


def chunk_record(doc_id: str, author: str, chunk: Chunk, target_words: int) -> dict:
    rec = asdict(chunk)
    rec.update({
        "doc_id": doc_id,
        "author": author,
        "chunk_id": f"{doc_id}__c{chunk.chunk_index:03d}",
        "target_words": target_words,
    })
    return rec


def parse_human_filename(path: Path) -> dict:
    """Human_<Author>_<TLGid>.txt -> {author, doc_id}."""
    stem = path.stem
    parts = stem.split("_")
    author = parts[1] if len(parts) >= 2 else "Unknown"
    return {"author": author, "doc_id": stem}
