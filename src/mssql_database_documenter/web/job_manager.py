"""Single-heavy-job manager with safe lifecycle, logs, progress and cancellation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import threading
import time
import uuid
from typing import Any, Callable

from ..redaction import redact_text


FINAL_STATUSES = frozenset({"COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED", "CANCELLED"})


@dataclass(slots=True)
class Job:
    id: str
    action: str
    database: str
    mode: str
    status: str = "QUEUED"
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_utc: str = ""
    finished_utc: str = ""
    current_stage: str = ""
    progress: int = 0
    warnings: list[str] = field(default_factory=list)
    error: str = ""
    logs: list[str] = field(default_factory=list)
    result: Any = None
    cancel_event: threading.Event = field(default_factory=threading.Event, repr=False)

    def public(self) -> dict[str, Any]:
        elapsed = 0.0
        if self.started_utc:
            start = datetime.fromisoformat(self.started_utc)
            end = datetime.fromisoformat(self.finished_utc) if self.finished_utc else datetime.now(timezone.utc)
            elapsed = round((end - start).total_seconds(), 2)
        return {"id": self.id, "action": self.action, "database": self.database, "mode": self.mode, "status": self.status, "created_utc": self.created_utc, "started_utc": self.started_utc, "finished_utc": self.finished_utc, "elapsed_seconds": elapsed, "current_stage": self.current_stage, "progress": self.progress, "warnings": self.warnings[-20:], "error": self.error, "logs": self.logs[-100:], "result": self.result}


class JobConflictError(RuntimeError):
    pass


class JobManager:
    def __init__(self, *, sensitive_values: tuple[str, ...] = ()) -> None:
        self._lock = threading.RLock(); self._jobs: dict[str, Job] = {}; self._current: str | None = None; self._sensitive_values = sensitive_values

    def _log(self, job: Job, message: object) -> None:
        job.logs.append(redact_text(message, sensitive_values=self._sensitive_values))

    def start(self, action: str, database: str, mode: str, target: Callable[[Job, Callable[[dict[str, Any]], None]], Any]) -> Job:
        with self._lock:
            current = self.current()
            if current and current.status not in FINAL_STATUSES: raise JobConflictError("A discovery/control job is already running")
            job = Job(uuid.uuid4().hex, action, database, mode); self._jobs[job.id] = job; self._current = job.id
        def update(event: dict[str, Any]) -> None:
            with self._lock:
                job.current_stage = str(event.get("stage") or job.current_stage)
                prompt = str(event.get("prompt") or "0"); job.progress = min(99, max(job.progress, int(prompt) * 4 if prompt.isdigit() else job.progress))
                self._log(job, f"{event.get('database', database)} | {prompt} | {job.current_stage} | {event.get('status', '')}")
        def runner() -> None:
            job.status = "RUNNING"; job.started_utc = datetime.now(timezone.utc).isoformat(); self._log(job, f"Started predefined action: {action}")
            try:
                job.result = target(job, update)
                if job.cancel_event.is_set(): job.status = "CANCELLED"
                else:
                    warning_count = len(job.warnings)
                    if isinstance(job.result, dict): warning_count += int(job.result.get("warning_count") or 0)
                    job.status = "COMPLETED_WITH_WARNINGS" if warning_count else "COMPLETED"
                    job.progress = 100
            except Exception as exc:
                if job.cancel_event.is_set() or exc.__class__.__name__ == "DiscoveryCancelled": job.status = "CANCELLED"
                else:
                    job.status = "FAILED"
                    job.error = redact_text(f"{type(exc).__name__}: {exc}", sensitive_values=self._sensitive_values)
                    self._log(job, job.error)
            finally:
                job.finished_utc = datetime.now(timezone.utc).isoformat(); self._log(job, f"Finished with status {job.status}")
        threading.Thread(target=runner, name=f"mssql-doc-{job.id[:8]}", daemon=True).start()
        return job

    def cancel(self, job_id: str) -> Job:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job: raise KeyError(job_id)
            if job.status in FINAL_STATUSES: return job
            job.cancel_event.set(); self._log(job, "Cancellation requested; the next safe stage boundary will stop execution")
            return job

    def get(self, job_id: str) -> Job | None:
        with self._lock: return self._jobs.get(job_id)

    def current(self) -> Job | None:
        with self._lock: return self._jobs.get(self._current) if self._current else None

    def wait(self, job_id: str, timeout: float = 10.0) -> Job:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            job = self.get(job_id)
            if job and job.status in FINAL_STATUSES: return job
            time.sleep(0.01)
        raise TimeoutError(job_id)
