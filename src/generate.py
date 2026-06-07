"""Generate Ancient Greek rewrites of human source chunks.

For each (system, prompt) condition, rewrite every human chunk with the chosen
LLM, enforcing length preservation (retry/repair when out of tolerance), and log
model id, parameters, token usage, attempts, and length ratio for every call.

Outputs:
    data/generated/<System><PromptSuffix>/<file>.txt   one rewrite per chunk
    output/logs/generation_log.jsonl                    one record per call

Usage:
    python src/generate.py --systems GPT5 Claude48 --prompts Restricted Free
    python src/generate.py --systems GPT5 --prompts Restricted --limit 8   # smoke test
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import config  # noqa: E402
from src.chunking import n_words  # noqa: E402
from src.normalize import normalize_greek  # noqa: E402

PROMPT_SUFFIX = {"Restricted": "", "Free": "Free"}


def _load_prompt(prompt_key: str) -> tuple[str, str]:
    raw = config.PROMPTS[prompt_key].read_text(encoding="utf-8")
    # Split "SYSTEM:\n...\n\nUSER:\n..."
    sys_part, user_part = raw.split("USER:", 1)
    sys_part = sys_part.replace("SYSTEM:", "", 1).strip()
    return sys_part, user_part.strip()


def _format_user(template: str, source_text: str) -> str:
    sw = n_words(source_text)
    lo = int(round(sw * (1 - config.LENGTH_TOLERANCE)))
    hi = int(round(sw * (1 + config.LENGTH_TOLERANCE)))
    return template.format(source_text=source_text, source_words=sw,
                           target_words=sw, min_words=lo, max_words=hi)


# --- API callers -----------------------------------------------------------
def _call_openai(model: str, system: str, user: str, params: dict) -> dict:
    from openai import OpenAI
    client = OpenAI()
    base = dict(model=model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}])
    # Newer OpenAI models use max_completion_tokens; some reject temperature/seed.
    optional = {"max_completion_tokens": params["max_output_tokens"]}
    if params.get("seed") is not None:
        optional["seed"] = params["seed"]
    if params.get("temperature") is not None:
        optional["temperature"] = params["temperature"]

    # Retry once dropping any parameter the model rejects as unsupported.
    for _ in range(len(optional) + 1):
        try:
            resp = client.chat.completions.create(**base, **optional)
            break
        except Exception as e:  # noqa: BLE001
            msg = str(e).lower()
            dropped = None
            for p in list(optional):
                if p.replace("_", " ") in msg or p in msg:
                    dropped = p; break
            if dropped is None and "max_tokens" in msg and "max_completion_tokens" in optional:
                # Older endpoint expects max_tokens
                optional["max_tokens"] = optional.pop("max_completion_tokens"); continue
            if dropped is None:
                raise
            optional.pop(dropped, None)
    return {"text": (resp.choices[0].message.content or "").strip(),
            "usage": {"in": resp.usage.prompt_tokens,
                      "out": resp.usage.completion_tokens}}


def _call_anthropic(model: str, system: str, user: str, params: dict) -> dict:
    import anthropic
    client = anthropic.Anthropic()
    base = dict(model=model, system=system, max_tokens=params["max_output_tokens"],
                messages=[{"role": "user", "content": user}])
    optional = {}
    if params.get("temperature") is not None:
        optional["temperature"] = params["temperature"]
    # Retry dropping any parameter the model rejects (e.g. temperature deprecated
    # on newer Claude models).
    for _ in range(len(optional) + 1):
        try:
            resp = client.messages.create(**base, **optional)
            break
        except Exception as e:  # noqa: BLE001
            msg = str(e).lower()
            dropped = next((p for p in list(optional) if p in msg), None)
            if dropped is None:
                raise
            optional.pop(dropped, None)
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    return {"text": text,
            "usage": {"in": resp.usage.input_tokens, "out": resp.usage.output_tokens}}


def _dispatch(system_key: str, system: str, user: str) -> dict:
    spec = config.MODELS[system_key]
    model = spec["model"]
    if spec["provider"] == "openai":
        return _call_openai(model, system, user, config.GEN_PARAMS) | {"model": model}
    return _call_anthropic(model, system, user, config.GEN_PARAMS) | {"model": model}


# --- Generation with length control ----------------------------------------
def generate_one(system_key: str, prompt_key: str, source_text: str,
                 max_retries: int = 3) -> dict:
    system, user_tmpl = _load_prompt(prompt_key)
    user = _format_user(user_tmpl, source_text)
    src_n = n_words(source_text)
    lo = src_n * (1 - config.LENGTH_TOLERANCE)
    hi = src_n * (1 + config.LENGTH_TOLERANCE)

    attempts = []
    text = ""
    for attempt in range(1, max_retries + 1):
        out = _dispatch(system_key, system, user)
        text = out["text"]
        out_n = n_words(text)
        ratio = out_n / src_n if src_n else 0.0
        attempts.append({"attempt": attempt, "out_words": out_n, "ratio": round(ratio, 3),
                         "usage": out["usage"]})
        if lo <= out_n <= hi or not text:
            break
        # Corrective follow-up instruction for the next attempt.
        direction = "longer" if out_n < lo else "shorter"
        user = (user_tmpl.format(source_text=source_text, source_words=src_n,
                                 target_words=src_n, min_words=int(lo), max_words=int(hi))
                + f"\n\nYour previous attempt had {out_n} words; make it {direction} "
                  f"so it falls within {int(lo)}-{int(hi)} words. Output ONLY the Greek text.")
    return {"text": text, "model": out["model"], "src_words": src_n,
            "final_words": n_words(text), "attempts": attempts,
            "in_tolerance": bool(lo <= n_words(text) <= hi)}


def _gen_filename(system_key: str, prompt_key: str, chunk_id: str) -> str:
    return f"{system_key}{PROMPT_SUFFIX[prompt_key]}_{chunk_id}.txt"


def run(systems: list[str], prompts: list[str], manifest_path: Path,
        limit: int | None = None) -> None:
    config.ensure_dirs()
    manifest = pd.read_csv(manifest_path)
    if limit:
        manifest = manifest.head(limit)
    log_path = config.LOGS_DIR / "generation_log.jsonl"
    log = open(log_path, "a", encoding="utf-8")

    for system_key in systems:
        for prompt_key in prompts:
            outdir = config.GEN_DIR / f"{system_key}{PROMPT_SUFFIX[prompt_key]}"
            outdir.mkdir(parents=True, exist_ok=True)
            for _, row in manifest.iterrows():
                fn = _gen_filename(system_key, prompt_key, row["chunk_id"])
                fpath = outdir / fn
                if fpath.exists() and fpath.stat().st_size > 0:
                    continue  # idempotent
                src = Path(row["chunk_path"]).read_text(encoding="utf-8")
                t0 = time.time()
                try:
                    res = generate_one(system_key, prompt_key, src)
                except Exception as e:
                    rec = {"ts": time.time(), "system": system_key, "prompt": prompt_key,
                           "chunk_id": row["chunk_id"], "error": repr(e)[:300]}
                    log.write(json.dumps(rec, ensure_ascii=False) + "\n"); log.flush()
                    print(f"  ERROR {system_key}/{prompt_key} {row['chunk_id']}: {e!r}")
                    continue
                fpath.write_text(normalize_greek(res["text"]), encoding="utf-8")
                rec = {"ts": time.time(), "elapsed_s": round(time.time() - t0, 2),
                       "system": system_key, "prompt": prompt_key,
                       "model": res["model"], "params": config.GEN_PARAMS,
                       "chunk_id": row["chunk_id"], "doc_id": row["doc_id"],
                       "author": row["author"], "src_words": res["src_words"],
                       "final_words": res["final_words"], "in_tolerance": res["in_tolerance"],
                       "n_attempts": len(res["attempts"]), "attempts": res["attempts"],
                       "file": str(fpath)}
                log.write(json.dumps(rec, ensure_ascii=False) + "\n"); log.flush()
                print(f"  {system_key}/{prompt_key} {row['chunk_id']}: "
                      f"{res['src_words']}->{res['final_words']} words "
                      f"(tol={'Y' if res['in_tolerance'] else 'N'}, tries={len(res['attempts'])})")
    log.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", nargs="+", default=config.NEW_SYSTEMS)
    ap.add_argument("--prompts", nargs="+", default=list(config.PROMPTS.keys()))
    ap.add_argument("--manifest", default=str(config.CHUNKS_DIR / "chunk_manifest.csv"))
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    run(args.systems, args.prompts, Path(args.manifest), args.limit)


if __name__ == "__main__":
    main()
