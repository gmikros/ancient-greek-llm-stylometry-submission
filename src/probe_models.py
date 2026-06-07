"""Resolve and validate LLM model identifiers against the live APIs.

Lists available OpenAI and Anthropic models, then tries to match the aliases in
configs.config.MODELS to concrete ids (exact match first, then a best-effort
prefix/contains match). Writes configs/resolved_models.json.

Usage:
    python src/probe_models.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import config  # noqa: E402


def list_openai() -> list[str]:
    try:
        from openai import OpenAI
        return sorted(m.id for m in OpenAI().models.list().data)
    except Exception as e:  # pragma: no cover - network dependent
        print(f"[openai] list error: {e!r}")
        return []


def list_anthropic() -> list[str]:
    try:
        import anthropic
        return [m.id for m in anthropic.Anthropic().models.list(limit=100).data]
    except Exception as e:  # pragma: no cover - network dependent
        print(f"[anthropic] list error: {e!r}")
        return []


def _resolve(requested: str, available: list[str]) -> dict:
    if requested in available:
        return {"requested": requested, "resolved": requested, "match": "exact"}
    # prefix match (e.g. "gpt-5.5" -> "gpt-5.5-2026-xx-xx")
    pref = [a for a in available if a.startswith(requested)]
    if pref:
        return {"requested": requested, "resolved": sorted(pref)[-1], "match": "prefix"}
    # contains match on normalized token
    norm = requested.replace(".", "").replace("-", "")
    contains = [a for a in available if norm in a.replace(".", "").replace("-", "")]
    if contains:
        return {"requested": requested, "resolved": sorted(contains)[-1], "match": "contains"}
    return {"requested": requested, "resolved": None, "match": "unresolved"}


def main() -> None:
    oai = list_openai()
    ant = list_anthropic()
    print(f"OpenAI models: {len(oai)} | Anthropic models: {len(ant)}")

    resolved = {}
    for key, spec in config.MODELS.items():
        avail = oai if spec["provider"] == "openai" else ant
        r = _resolve(spec["model"], avail)
        r["provider"] = spec["provider"]
        resolved[key] = r
        print(f"  {key:9s} [{spec['provider']:9s}] {spec['model']:28s} -> "
              f"{r['resolved']} ({r['match']})")

    out = config.REPO_ROOT / "configs" / "resolved_models.json"
    out.write_text(json.dumps(
        {"openai_available": oai, "anthropic_available": ant, "resolved": resolved},
        indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
