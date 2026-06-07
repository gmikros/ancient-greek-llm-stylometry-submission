"""Batch-API generation of Ancient Greek rewrites (OpenAI + Anthropic).

This mirrors the synchronous generator (src/generate.py) but submits every
(system, prompt, chunk) request through the providers' asynchronous batch APIs
(~50% cheaper, 24h window). Prompts are built with the *exact same* helpers as
the sync path so the conditions are identical.

Conditions (new models only, no longitudinal):
    systems = ["GPT5", "Claude48"], prompts = ["Restricted", "Free"]  -> 4 batches,
    each over ALL chunks in data/chunks/size_400/chunk_manifest.csv.

Subcommands:
    python src/generate_batch.py submit                 # build + submit the 4 batches
    python src/generate_batch.py submit --dry-run        # build request JSONL only
    python src/generate_batch.py status                  # poll each batch
    python src/generate_batch.py collect                 # download + write rewrites + log
    python src/generate_batch.py resubmit-corrections    # rebuild out-of-tolerance items

Notes:
    Batch requests cannot drop-and-retry rejected params, so we never send
    temperature/seed. OpenAI uses max_completion_tokens=16384; Anthropic uses
    max_tokens=8192 (400-word Greek + reasoning tokens can be long; output is
    billed per token actually produced).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from statistics import median

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import config  # noqa: E402
from src.chunking import n_words  # noqa: E402
from src.normalize import normalize_greek  # noqa: E402
from src.generate import _load_prompt, _format_user, PROMPT_SUFFIX  # noqa: E402

# Logs contain Greek; force UTF-8 stdout.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

SYSTEMS = list(config.NEW_SYSTEMS)          # ["GPT5", "Claude48"]
PROMPTS = list(config.PROMPTS.keys())        # ["Restricted", "Free"]

OPENAI_MAX_COMPLETION_TOKENS = 16384
ANTHROPIC_MAX_TOKENS = 8192

BATCH_DIR = config.GEN_DIR / "_batches"
REGISTRY_PATH = BATCH_DIR / "batches.json"


# --- Registry --------------------------------------------------------------
def _load_registry() -> list[dict]:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return []
    return []


def _save_registry(registry: list[dict]) -> None:
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2),
                             encoding="utf-8")


# --- Request building ------------------------------------------------------
# Separator valid for BOTH providers: Anthropic requires custom_id to match
# ^[a-zA-Z0-9_-]{1,64}$ (so "|" is rejected). System/prompt names contain no
# "-", and chunk_ids contain no "-", so "-" is an unambiguous separator.
SEP = "-"


def _custom_id(system: str, prompt: str, chunk_id: str) -> str:
    return f"{system}{SEP}{prompt}{SEP}{chunk_id}"


def _chunk_id_from_cid(cid: str, system: str, prompt: str) -> str:
    """Recover chunk_id from a custom_id, tolerant of the legacy "|" separator."""
    for sep in (SEP, "|"):
        prefix = f"{system}{sep}{prompt}{sep}"
        if cid.startswith(prefix):
            return cid[len(prefix):]
    # Fallback: strip the first two separator-delimited fields.
    for sep in (SEP, "|"):
        if cid.count(sep) >= 2:
            return cid.split(sep, 2)[2]
    return cid


def _openai_request(custom_id: str, model: str, system_text: str, user: str) -> dict:
    return {"custom_id": custom_id, "method": "POST", "url": "/v1/chat/completions",
            "body": {"model": model,
                     "messages": [{"role": "system", "content": system_text},
                                  {"role": "user", "content": user}],
                     "max_completion_tokens": OPENAI_MAX_COMPLETION_TOKENS}}


def _anthropic_request(custom_id: str, model: str, system_text: str, user: str) -> dict:
    return {"custom_id": custom_id,
            "params": {"model": model, "system": system_text,
                       "max_tokens": ANTHROPIC_MAX_TOKENS,
                       "messages": [{"role": "user", "content": user}]}}


def _build_requests(manifest: pd.DataFrame, system: str, prompt: str) -> list[dict]:
    """Build the full request list for one (system, prompt) condition."""
    provider = config.MODELS[system]["provider"]
    model = config.MODELS[system]["model"]
    system_text, user_tmpl = _load_prompt(prompt)
    reqs = []
    for _, row in manifest.iterrows():
        src = Path(row["chunk_path"]).read_text(encoding="utf-8")
        user = _format_user(user_tmpl, src)
        cid = _custom_id(system, prompt, str(row["chunk_id"]))
        if provider == "openai":
            reqs.append(_openai_request(cid, model, system_text, user))
        else:
            reqs.append(_anthropic_request(cid, model, system_text, user))
    return reqs


# --- Submit ----------------------------------------------------------------
def _submit_one(provider: str, system: str, prompt: str, reqs: list[dict],
                registry: list[dict], dry_run: bool = False,
                kind: str = "initial", tag: str = "") -> dict | None:
    """Submit one batch (or write JSONL only on dry-run). Saves registry on success."""
    n = len(reqs)
    if n == 0:
        print(f"  [skip] {provider} {system}/{prompt}{tag}: 0 requests")
        return None
    fsuffix = f"_{tag}" if tag else ""
    print(f"[submit] {provider} {system}/{prompt}{tag}: {n} requests")

    if provider == "openai":
        jsonl_path = BATCH_DIR / f"openai_{system}_{prompt}{fsuffix}_requests.jsonl"
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with open(jsonl_path, "w", encoding="utf-8") as fh:
            for r in reqs:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        if dry_run:
            print(f"  [dry-run] wrote {jsonl_path.name} ({n} lines); not uploading.")
            return None
        try:
            from openai import OpenAI
            client = OpenAI()
            with open(jsonl_path, "rb") as fh:
                up = client.files.create(file=fh, purpose="batch")
            batch = client.batches.create(input_file_id=up.id,
                                           endpoint="/v1/chat/completions",
                                           completion_window="24h")
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR submitting openai {system}/{prompt}: {e!r}")
            return None
        entry = {"provider": "openai", "system": system, "prompt": prompt,
                 "batch_id": batch.id, "n_requests": n,
                 "input_file": str(jsonl_path), "submitted_ts": time.time(),
                 "kind": kind}
    else:  # anthropic
        if dry_run:
            jsonl_path = BATCH_DIR / f"anthropic_{system}_{prompt}{fsuffix}_requests.jsonl"
            jsonl_path.parent.mkdir(parents=True, exist_ok=True)
            with open(jsonl_path, "w", encoding="utf-8") as fh:
                for r in reqs:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"  [dry-run] wrote {jsonl_path.name} ({n} lines); not submitting.")
            return None
        try:
            import anthropic
            client = anthropic.Anthropic()
            batch = client.messages.batches.create(requests=reqs)
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR submitting anthropic {system}/{prompt}: {e!r}")
            return None
        entry = {"provider": "anthropic", "system": system, "prompt": prompt,
                 "batch_id": batch.id, "n_requests": n,
                 "input_file": None, "submitted_ts": time.time(),
                 "kind": kind}

    registry.append(entry)
    _save_registry(registry)  # save incrementally; never lose a submitted id
    print(f"  submitted {provider} batch {entry['batch_id']} ({n} requests)")
    return entry


def submit(manifest_path: Path, dry_run: bool = False, limit: int | None = None) -> None:
    config.ensure_dirs()
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(manifest_path)
    if limit:
        manifest = manifest.head(limit)
    print(f"Manifest: {manifest_path}  ({len(manifest)} chunks)")
    registry = _load_registry()
    already = {(e["system"], e["prompt"]) for e in registry
               if e.get("kind", "initial") == "initial"}
    for system in SYSTEMS:
        provider = config.MODELS[system]["provider"]
        for prompt in PROMPTS:
            if not dry_run and (system, prompt) in already:
                print(f"[skip] {provider} {system}/{prompt}: already submitted "
                      f"(in registry); not resubmitting.")
                continue
            reqs = _build_requests(manifest, system, prompt)
            _submit_one(provider, system, prompt, reqs, registry, dry_run=dry_run)
    if not dry_run:
        print(f"\nRegistry: {REGISTRY_PATH}  ({len(registry)} batches total)")


# --- Status ----------------------------------------------------------------
def status() -> None:
    registry = _load_registry()
    if not registry:
        print("No batches in registry.")
        return
    for entry in registry:
        provider, bid = entry["provider"], entry["batch_id"]
        label = f"{entry['system']}/{entry['prompt']} ({entry.get('kind', 'initial')})"
        try:
            if provider == "openai":
                from openai import OpenAI
                b = OpenAI().batches.retrieve(bid)
                rc = b.request_counts
                print(f"openai     {label} {bid}: {b.status} "
                      f"[total={rc.total} completed={rc.completed} failed={rc.failed}]")
            else:
                import anthropic
                b = anthropic.Anthropic().messages.batches.retrieve(bid)
                rc = b.request_counts
                print(f"anthropic  {label} {bid}: {b.processing_status} "
                      f"[processing={rc.processing} succeeded={rc.succeeded} "
                      f"errored={rc.errored} canceled={rc.canceled} expired={rc.expired}]")
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR status {provider} {bid}: {e!r}")


# --- Collect ---------------------------------------------------------------
def _openai_results(client, batch_id: str):
    """Yield (custom_id, text, usage_in, usage_out, model, err) for a completed batch."""
    b = client.batches.retrieve(batch_id)
    if b.status != "completed":
        print(f"openai {batch_id} not completed (status={b.status}); skipping.")
        return
    if not b.output_file_id:
        print(f"openai {batch_id} has no output_file_id; skipping.")
        return
    content = client.files.content(b.output_file_id).text
    for line in content.splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        cid = obj.get("custom_id", "")
        err = obj.get("error")
        resp = obj.get("response") or {}
        body = resp.get("body") or {}
        text, uin, uout = "", 0, 0
        model = ""
        if body:
            try:
                text = (body["choices"][0]["message"]["content"] or "").strip()
            except Exception:  # noqa: BLE001
                text = ""
            usage = body.get("usage") or {}
            uin = usage.get("prompt_tokens", 0)
            uout = usage.get("completion_tokens", 0)
            model = body.get("model", "")
        yield cid, text, uin, uout, model, err


def _anthropic_results(client, batch_id: str):
    b = client.messages.batches.retrieve(batch_id)
    if b.processing_status != "ended":
        print(f"anthropic {batch_id} not ended (status={b.processing_status}); skipping.")
        return
    for result in client.messages.batches.results(batch_id):
        cid = result.custom_id
        text, uin, uout, model, err = "", 0, 0, "", None
        rtype = result.result.type
        if rtype == "succeeded":
            msg = result.result.message
            text = "".join(blk.text for blk in msg.content
                           if getattr(blk, "type", "") == "text").strip()
            uin = msg.usage.input_tokens
            uout = msg.usage.output_tokens
            model = msg.model
        else:
            err = rtype
        yield cid, text, uin, uout, model, err


def collect(manifest_path: Path) -> int:
    """Download finished batches, write+log rewrites, return #files written.

    Idempotent: a rewrite whose .txt already exists and is non-empty is skipped
    (not re-written and not re-logged), so collect can be run repeatedly (e.g. by
    the reboot-proof scheduler) without duplicating files or log lines.
    """
    config.ensure_dirs()
    manifest = pd.read_csv(manifest_path)
    minfo = {str(r["chunk_id"]): r for _, r in manifest.iterrows()}
    registry = _load_registry()
    if not registry:
        print("No batches in registry.")
        return 0

    log_path = config.LOGS_DIR / "generation_log.jsonl"
    log = open(log_path, "a", encoding="utf-8")
    summary: dict[tuple[str, str], list[tuple[float, bool]]] = defaultdict(list)
    total_written = 0
    total_skipped = 0

    for entry in registry:
        provider, bid = entry["provider"], entry["batch_id"]
        system, prompt = entry["system"], entry["prompt"]
        suffix = PROMPT_SUFFIX[prompt]
        outdir = config.GEN_DIR / f"{system}{suffix}"
        outdir.mkdir(parents=True, exist_ok=True)

        try:
            if provider == "openai":
                from openai import OpenAI
                results = _openai_results(OpenAI(), bid)
            else:
                import anthropic
                results = _anthropic_results(anthropic.Anthropic(), bid)
            results = list(results)
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR collecting {provider} {bid}: {e!r}")
            continue

        written = 0
        skipped = 0
        for cid, text, uin, uout, model, err in results:
            chunk_id = _chunk_id_from_cid(cid, system, prompt)
            row = minfo.get(str(chunk_id))
            src_words = int(row["n_words"]) if row is not None else 0
            doc_id = str(row["doc_id"]) if row is not None else ""
            author = str(row["author"]) if row is not None else ""
            # Normalize AI output to the source-corpus convention.
            text = normalize_greek(text)
            if not text:
                print(f"  SKIP empty/failed {provider} {system}/{prompt} {chunk_id} (err={err})")
                continue
            fpath = outdir / f"{system}{suffix}_{chunk_id}.txt"
            # Idempotency: skip files that already exist and are non-empty so
            # repeated collect runs neither rewrite files nor duplicate logs.
            if fpath.exists() and fpath.stat().st_size > 0:
                skipped += 1
                continue
            fpath.write_text(text, encoding="utf-8")
            written += 1
            fw = n_words(text)
            ratio = fw / src_words if src_words else 0.0
            lo = src_words * (1 - config.LENGTH_TOLERANCE)
            hi = src_words * (1 + config.LENGTH_TOLERANCE)
            in_tol = bool(lo <= fw <= hi)
            rec = {"ts": time.time(), "system": system, "prompt": prompt,
                   "model": model or config.MODELS[system]["model"],
                   "chunk_id": chunk_id, "doc_id": doc_id, "author": author,
                   "src_words": src_words, "final_words": fw,
                   "in_tolerance": in_tol, "usage": {"in": uin, "out": uout},
                   "batch_id": bid}
            log.write(json.dumps(rec, ensure_ascii=False) + "\n")
            summary[(system, prompt)].append((ratio, in_tol))
        log.flush()
        total_written += written
        total_skipped += skipped
        print(f"collected {provider} {system}/{prompt} {bid}: wrote {written} files"
              f" (skipped {skipped} already-present)")
    log.close()

    print("\n=== Collection summary (per condition) ===")
    for (system, prompt), vals in sorted(summary.items()):
        n = len(vals)
        tol_rate = (sum(1 for _, t in vals if t) / n) if n else 0.0
        med = median([r for r, _ in vals]) if vals else 0.0
        print(f"{system}/{prompt}: count={n}  in_tolerance={tol_rate:.1%}  "
              f"median_length_ratio={med:.3f}")
    print(f"TOTAL written this run: {total_written}  (skipped already-present: {total_skipped})")
    return total_written


# --- Resubmit corrections --------------------------------------------------
def resubmit_corrections(manifest_path: Path, dry_run: bool = False) -> None:
    config.ensure_dirs()
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(manifest_path)
    minfo = {str(r["chunk_id"]): r for _, r in manifest.iterrows()}

    log_path = config.LOGS_DIR / "generation_log.jsonl"
    if not log_path.exists():
        print("No generation_log.jsonl yet; nothing to correct.")
        return

    # Keep the latest in_tolerance verdict per (system, prompt, chunk_id).
    failing: dict[tuple[str, str, str], dict] = {}
    with open(log_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            if "in_tolerance" not in rec or "chunk_id" not in rec:
                continue
            key = (rec.get("system"), rec.get("prompt"), str(rec.get("chunk_id")))
            if rec.get("in_tolerance"):
                failing.pop(key, None)
            else:
                failing[key] = rec
    if not failing:
        print("No out-of-tolerance items to resubmit.")
        return

    groups: dict[tuple[str, str], list[tuple[str, int]]] = defaultdict(list)
    for (system, prompt, chunk_id), rec in failing.items():
        groups[(system, prompt)].append((chunk_id, int(rec.get("final_words", 0))))

    registry = _load_registry()
    for (system, prompt), chunks in groups.items():
        provider = config.MODELS[system]["provider"]
        model = config.MODELS[system]["model"]
        system_text, user_tmpl = _load_prompt(prompt)
        reqs = []
        for chunk_id, prev_words in chunks:
            row = minfo.get(str(chunk_id))
            if row is None:
                continue
            src = Path(row["chunk_path"]).read_text(encoding="utf-8")
            sw = n_words(src)
            lo = int(round(sw * (1 - config.LENGTH_TOLERANCE)))
            hi = int(round(sw * (1 + config.LENGTH_TOLERANCE)))
            direction = "longer" if prev_words < lo else "shorter"
            user = _format_user(user_tmpl, src)
            user += (f"\n\nYour previous attempt had {prev_words} words; make it {direction} "
                     f"to fall within {lo}-{hi} words. Output ONLY the Greek text.")
            cid = _custom_id(system, prompt, str(chunk_id))
            if provider == "openai":
                reqs.append(_openai_request(cid, model, system_text, user))
            else:
                reqs.append(_anthropic_request(cid, model, system_text, user))
        _submit_one(provider, system, prompt, reqs, registry, dry_run=dry_run,
                    kind="correction", tag="corr")


# --- CLI -------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Batch-API generation (OpenAI + Anthropic).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    default_manifest = str(config.CHUNKS_DIR / "size_400" / "chunk_manifest.csv")

    p_sub = sub.add_parser("submit", help="Build + submit the 4 batches.")
    p_sub.add_argument("--manifest", default=default_manifest)
    p_sub.add_argument("--dry-run", action="store_true",
                       help="Write request JSONL only; do not upload/submit.")
    p_sub.add_argument("--limit", type=int, default=None,
                       help="Only the first N chunks (for smoke tests).")

    sub.add_parser("status", help="Poll each registered batch.")

    p_col = sub.add_parser("collect", help="Download results, write rewrites, log.")
    p_col.add_argument("--manifest", default=default_manifest)

    p_corr = sub.add_parser("resubmit-corrections",
                            help="Rebuild + submit out-of-tolerance items.")
    p_corr.add_argument("--manifest", default=default_manifest)
    p_corr.add_argument("--dry-run", action="store_true")

    args = ap.parse_args()
    if args.cmd == "submit":
        submit(Path(args.manifest), dry_run=args.dry_run, limit=args.limit)
    elif args.cmd == "status":
        status()
    elif args.cmd == "collect":
        collect(Path(args.manifest))
    elif args.cmd == "resubmit-corrections":
        resubmit_corrections(Path(args.manifest), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
