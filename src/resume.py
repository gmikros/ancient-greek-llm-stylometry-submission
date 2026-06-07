"""Reboot-proof, idempotent resume driver for the batch generation run.

The OpenAI/Anthropic batches execute server-side, so a local shutdown or reboot
never loses them. This script just needs to run periodically and, once the
batches finish, COLLECT their outputs exactly once. It is safe to run repeatedly
(by a Windows Scheduled Task; see docs/BATCH_RUN.md):

  * single-instance guard via a lockfile (output/logs/resume.lock); if the lock
    exists and is fresh (< 25 min old) another run is assumed in progress and we
    exit quietly,
  * runs the equivalent of `generate_batch.py status` then `... collect`
    (collect skips rewrite files that already exist and are non-empty, so no
    file is written or logged twice),
  * appends one timestamped summary line to output/logs/resume.log,
  * ALWAYS exits 0 (never throws) so the scheduler keeps firing.
"""
from __future__ import annotations

import contextlib
import datetime
import io
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from configs import config  # noqa: E402

LOCK_MAX_AGE_SEC = 25 * 60  # treat a lock younger than this as "run in progress"
MANIFEST = config.CHUNKS_DIR / "size_400" / "chunk_manifest.csv"


def _now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _append_log(line: str) -> None:
    try:
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(config.LOGS_DIR / "resume.log", "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:  # noqa: BLE001
        pass


def main() -> int:
    try:
        config.ensure_dirs()
    except Exception:  # noqa: BLE001
        pass

    lock = config.LOGS_DIR / "resume.lock"

    # --- Single-instance guard ---------------------------------------------
    if lock.exists():
        try:
            age = time.time() - lock.stat().st_mtime
        except Exception:  # noqa: BLE001
            age = LOCK_MAX_AGE_SEC + 1  # unreadable -> treat as stale
        if age < LOCK_MAX_AGE_SEC:
            return 0  # another run is in progress; exit quietly
        # otherwise the lock is stale; we take it over below

    try:
        lock.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    try:
        import src.generate_batch as gb  # imported here so import errors are caught

        # --- status (capture output for the log) ---------------------------
        status_buf = io.StringIO()
        with contextlib.redirect_stdout(status_buf):
            try:
                gb.status()
            except Exception as e:  # noqa: BLE001
                print(f"status ERROR: {e!r}")
        status_text = status_buf.getvalue().strip()

        # --- collect (idempotent; skips existing non-empty rewrites) -------
        collected = 0
        collect_buf = io.StringIO()
        with contextlib.redirect_stdout(collect_buf):
            try:
                if MANIFEST.exists():
                    collected = gb.collect(MANIFEST) or 0
                else:
                    print(f"manifest missing: {MANIFEST}")
            except Exception as e:  # noqa: BLE001
                print(f"collect ERROR: {e!r}")

        status_oneline = " || ".join(
            ln.strip() for ln in status_text.splitlines() if ln.strip()
        ) or "(no batches / no status)"
        _append_log(
            f"[{_now()}] collected={collected} file(s) this run; "
            f"statuses: {status_oneline}"
        )
    except Exception as e:  # noqa: BLE001
        _append_log(f"[{_now()}] FATAL (handled): {e!r}")
    finally:
        try:
            lock.unlink()
        except Exception:  # noqa: BLE001
            pass

    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    # Never throw: the scheduler must keep working across reboots.
    try:
        code = main()
    except Exception:  # noqa: BLE001
        code = 0
    sys.exit(code if isinstance(code, int) else 0)
