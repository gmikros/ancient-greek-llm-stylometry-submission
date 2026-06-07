"""Greek normalization to match the human source-corpus conventions.

The human orator source texts are: lowercase, retain polytonic DIACRITICS
(accents/breathings), carry NO punctuation, and have no elision apostrophes
(e.g. "οὔτ ἐν", never "οὔτ' ἐν"). To keep released human chunks and model
rewrites on identical footing, every text passes through ``normalize_greek``.

``normalize_greek`` is idempotent: running it twice yields the same result as
running it once. Removed characters (punctuation + apostrophes/elision marks)
are replaced with a space and runs of whitespace are then collapsed, so an
elided "δ'αὐτὸν" becomes "δ αὐτὸν" -- matching the source convention rather
than gluing the words together.
"""
from __future__ import annotations

import re
import unicodedata

# ASCII punctuation (includes the straight apostrophe U+0027 and the hyphen).
_ASCII_PUNCT = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""

# Greek- and Unicode-specific punctuation, quotes, dashes, apostrophe/elision
# marks, and the STANDALONE (spacing) tonos marks. Combining diacritics that
# live inside precomposed letters (after NFC) are NOT listed here, so genuine
# accents/breathings are preserved.
_EXTRA_PUNCT = (
    "\u00b7"  # middle dot / ano teleia
    "\u0387"  # Greek ano teleia (NFC-decomposes to U+00B7; kept defensively)
    "\u037e"  # Greek question mark (looks like ';')
    "\u0384"  # Greek tonos (standalone, spacing)
    "\u0385"  # Greek dialytika tonos (standalone, spacing)
    "\u2010\u2011\u2012\u2013\u2014\u2015"  # hyphens / dashes
    "\u2018\u2019\u201a\u201b"  # single quotes (incl. U+2019 right single quote)
    "\u201c\u201d\u201e\u201f"  # double quotes
    "\u00ab\u00bb\u2039\u203a"  # guillemets
    "\u2026"  # horizontal ellipsis
    "\u00b4\u0060"  # standalone acute / grave
    "\u02bc"  # modifier letter apostrophe
    "\u02bb"  # modifier letter turned comma
    "\u1fbd"  # Greek koronis (elision mark)
)

_REMOVE_CHARS = sorted(set(_ASCII_PUNCT) | set(_EXTRA_PUNCT))
_REMOVE_RE = re.compile("[" + re.escape("".join(_REMOVE_CHARS)) + "]")
_WS_RE = re.compile(r"\s+")


def normalize_greek(text: str) -> str:
    """Normalize Greek text to the source-corpus convention.

    Steps: NFC normalize -> lowercase (polytonic-aware via ``str.lower``) ->
    remove punctuation and apostrophes/elision marks (replaced with a space) ->
    collapse whitespace and strip. Diacritics (accents/breathings) are kept.
    Idempotent.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    text = _REMOVE_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


if __name__ == "__main__":
    sample = "Ὦ ἄνδρες, Ἀθηναῖοι· οὔτ' ἐν εὐθύναις — “λόγος”; (Δ’ αὐτὸν)."
    once = normalize_greek(sample)
    twice = normalize_greek(once)
    print("BEFORE:", sample)
    print("AFTER :", once)
    print("IDEMPOTENT:", once == twice)
