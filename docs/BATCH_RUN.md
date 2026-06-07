# Batch-API generation run (size-400 chunks)

This documents the asynchronous batch generation of Ancient Greek rewrites for
the two **new** systems, using each provider's Batch API (~50% cheaper than the
synchronous path, with a 24-hour completion window).

## What gets submitted

Conditions are the two new models crossed with the two prompts (no longitudinal
older models), each over **all** chunks in
`data/chunks/size_400/chunk_manifest.csv`:

| Provider  | System    | Model              | Prompt     |
|-----------|-----------|--------------------|------------|
| OpenAI    | GPT5      | `gpt-5.5`          | Restricted |
| OpenAI    | GPT5      | `gpt-5.5`          | Free       |
| Anthropic | Claude48  | `claude-opus-4-8`  | Restricted |
| Anthropic | Claude48  | `claude-opus-4-8`  | Free       |

That is **4 batches** (one per system x prompt), each containing one request per
chunk. `custom_id = "{system}|{prompt}|{chunk_id}"`.

Prompts are built with the same `_load_prompt` / `_format_user` helpers as the
synchronous generator (`src/generate.py`), so the conditions are identical.

### Parameters (batch-specific)

Batch requests cannot drop-and-retry rejected parameters, so we **never send**
`temperature` or `seed`:

- **OpenAI** body: `{"model", "messages", "max_completion_tokens": 16384}`
- **Anthropic** params: `{"model", "system", "max_tokens": 8192, "messages": [...]}`

The larger token caps account for 400-word Greek plus `gpt-5.5` reasoning
tokens; output is billed per token actually produced.

## Registry

Every submitted batch is appended to `data/generated/_batches/batches.json`:

```json
{"provider", "system", "prompt", "batch_id", "n_requests", "input_file", "submitted_ts", "kind"}
```

This file is **tracked in git**; the large request `*.jsonl` files under
`data/generated/_batches/` are git-ignored.

## Commands

Submit the 4 batches (already done for the size-400 run):

```bash
python src/generate_batch.py submit
```

Check status / progress counts at any time:

```bash
python src/generate_batch.py status
```

Once the batches show as completed/ended (up to 24h), collect the results:

```bash
python src/generate_batch.py collect
```

`collect` writes each rewrite to
`data/generated/<System><PromptSuffix>/<System><PromptSuffix>_<chunk_id>.txt`
(skipping empty/failed items), appends one JSON line per item to
`output/logs/generation_log.jsonl`, and prints a per-condition summary (count,
in-tolerance rate, median length ratio).

## The 24-hour async window

Batches are processed asynchronously and may take up to 24 hours. You do **not**
need to keep a process running: submit, note the batch IDs (saved in the
registry), and return later to `status` / `collect`.

## Resubmit corrections (length tolerance)

Some rewrites land outside the +/-15% length tolerance. After collecting, you
can rebuild a corrective batch for the out-of-tolerance items:

```bash
python src/generate_batch.py resubmit-corrections
```

This scans `output/logs/generation_log.jsonl` for `in_tolerance == False`
(latest verdict per chunk), appends a corrective instruction to the user prompt
("Your previous attempt had N words; make it longer/shorter to fall within
{min}-{max} words. Output ONLY the Greek text."), and submits new batches that
are recorded in the registry (`kind: "correction"`). Re-run `collect` afterwards
to overwrite the corrected rewrites and log the new verdicts.

## Greek normalization

Both the released human chunks and the collected AI rewrites are passed through
`normalize_greek` (`src/normalize.py`) so they share the source-corpus
convention: **lowercase**, **polytonic diacritics kept**, **no punctuation**,
**no elision apostrophes** (`οὔτ ἐν`, never `οὔτ' ἐν`). It NFC-normalizes,
lowercases, replaces punctuation/quotes/dashes/apostrophes with a space, then
collapses whitespace. It is idempotent. `collect` normalizes each rewrite before
writing its `.txt` and before computing `final_words`; `build_chunks.py`
normalizes every human chunk before writing and before counting words;
`extract_features.py` and `embed.py` re-normalize defensively on read.

## Reboot-proof resume (scheduled task)

Because the batches run **server-side**, a local shutdown or reboot never loses
them. `src/resume.py` only needs to run periodically and, once a batch finishes,
collect its outputs **once**. It is fully idempotent:

- a lockfile (`output/logs/resume.lock`) guards against overlapping runs (a lock
  younger than 25 minutes means a run is already in progress, so it exits
  quietly);
- it runs the equivalent of `generate_batch.py status` then `... collect`
  (`collect` **skips** any rewrite `.txt` that already exists and is non-empty,
  so files and log lines are never duplicated);
- it appends one timestamped summary line (statuses + files collected this run)
  to `output/logs/resume.log`;
- it **always exits 0** so the scheduler keeps firing.

### What the scheduled task does

`scripts\resume_task.cmd` cd's into the repo and runs the system Python on
`src\resume.py`, appending stdout/stderr to `output\logs\resume.log`. Two
triggers are used (split into two tasks because `schtasks` cannot attach both a
minute and a logon trigger to one task):

| Task | Trigger | Purpose |
|------|---------|---------|
| `AG_BatchResume_Every30` | every 30 minutes | periodic poll + collect |
| `AG_BatchResume_OnLogon` | at user logon | resume promptly after a reboot |

The minute task already covers reboots within 30 minutes; the logon task just
makes resumption immediate.

### Create

```bat
schtasks /create /tn AG_BatchResume_Every30 /sc minute /mo 30 /f /tr "C:\Users\USER01\Dropbox\Workplace\D\George\PAPERS\Paroysiaseis\Cyprus 2025\ag-llm-stylometry\scripts\resume_task.cmd"

REM The logon trigger needs an ELEVATED (Run as administrator) shell:
schtasks /create /tn AG_BatchResume_OnLogon /sc onlogon /f /tr "C:\Users\USER01\Dropbox\Workplace\D\George\PAPERS\Paroysiaseis\Cyprus 2025\ag-llm-stylometry\scripts\resume_task.cmd"
```

> Note: `AG_BatchResume_Every30` was created successfully from a normal shell.
> `AG_BatchResume_OnLogon` returned `ERROR: Access is denied.` and must be
> created from an **elevated** Command Prompt / PowerShell (right-click → *Run as
> administrator*) using the second command above.

### View

```bat
schtasks /query /tn AG_BatchResume_Every30
schtasks /query /tn AG_BatchResume_OnLogon
```

### Remove (after the run is fully collected)

```bat
schtasks /delete /tn AG_BatchResume_Every30 /f
schtasks /delete /tn AG_BatchResume_OnLogon /f
```
