"""Background scheduler: daily NAV refresh and monthly recurring tranche runner.

Uses APScheduler's AsyncIOScheduler so the jobs share the FastAPI event loop.
Times are in Asia/Kolkata since AMFI publishes NAVAll.txt around 22:00 IST.

Jobs:
- fetch_nav: daily at 22:30 IST. Runs scripts/fetch_nav.py against data/market.db.
- recurring: 6th of every month at 08:00 IST. Runs recurring_runner.py then
  render_portfolio.py --write so portfolio.md Section 1.5 stays current.

The user can disable the whole scheduler via Settings.daily_nav_enabled. When
disabled, jobs are removed; when re-enabled, jobs are re-added. Manual "run
now" is exposed via the REST API.
"""

import asyncio
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from . import config, settings

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
LOG_DIR = config.PROJECT_ROOT / "data" / "logs"


@dataclass
class JobRun:
    started_at: str
    finished_at: str | None = None
    status: str = "running"  # running | success | failed
    exit_code: int | None = None
    output_tail: str = ""


@dataclass
class JobState:
    id: str
    description: str
    last_run: JobRun | None = None
    history: list[JobRun] = field(default_factory=list)


class Scheduler:
    DAILY_NAV_ID = "fetch_nav"
    RECURRING_ID = "recurring_runner"

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler(timezone=IST)
        self.jobs: dict[str, JobState] = {
            self.DAILY_NAV_ID: JobState(
                id=self.DAILY_NAV_ID,
                description="Daily AMFI NAV refresh (22:30 IST)",
            ),
            self.RECURRING_ID: JobState(
                id=self.RECURRING_ID,
                description="Monthly SIP/STP tranche generator (6th, 08:00 IST)",
            ),
        }
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self.scheduler.start()
        self._started = True
        self.sync_with_settings()
        logger.info("Scheduler started")

    def shutdown(self) -> None:
        if not self._started:
            return
        try:
            self.scheduler.shutdown(wait=False)
        except Exception:
            logger.exception("Error shutting down scheduler")
        self._started = False

    def sync_with_settings(self) -> None:
        """Reconcile jobs with current settings. Idempotent."""
        s = settings.load()
        if s.daily_nav_enabled:
            self._ensure_job(
                self.DAILY_NAV_ID,
                self._run_fetch_nav,
                CronTrigger(hour=22, minute=30, timezone=IST),
            )
            self._ensure_job(
                self.RECURRING_ID,
                self._run_recurring,
                CronTrigger(day=6, hour=8, minute=0, timezone=IST),
            )
        else:
            for job_id in (self.DAILY_NAV_ID, self.RECURRING_ID):
                self._remove_job(job_id)

    def _ensure_job(self, job_id: str, func, trigger) -> None:
        existing = self.scheduler.get_job(job_id)
        if existing is None:
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                max_instances=1,
                coalesce=True,
                replace_existing=True,
            )

    def _remove_job(self, job_id: str) -> None:
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    def status(self) -> dict[str, Any]:
        s = settings.load()
        result: dict[str, Any] = {
            "enabled": s.daily_nav_enabled,
            "jobs": [],
        }
        for state in self.jobs.values():
            apscheduler_job = self.scheduler.get_job(state.id) if self._started else None
            next_run = (
                apscheduler_job.next_run_time.isoformat()
                if apscheduler_job and apscheduler_job.next_run_time
                else None
            )
            result["jobs"].append(
                {
                    "id": state.id,
                    "description": state.description,
                    "next_run": next_run,
                    "scheduled": apscheduler_job is not None,
                    "last_run": _serialize_run(state.last_run),
                    "history": [_serialize_run(r) for r in state.history[-5:]],
                }
            )
        return result

    async def trigger(self, job_id: str) -> None:
        if job_id == self.DAILY_NAV_ID:
            await self._run_fetch_nav()
        elif job_id == self.RECURRING_ID:
            await self._run_recurring()
        else:
            raise ValueError(f"Unknown job: {job_id}")

    async def _run_fetch_nav(self) -> None:
        await self._run_python_script(
            self.DAILY_NAV_ID,
            ["scripts/fetch_nav.py", "--quiet"],
            log_filename="fetch_nav.log",
        )

    async def _run_recurring(self) -> None:
        # Two scripts back-to-back. recurring_runner first; if it succeeds,
        # render_portfolio updates Section 1.5 of portfolio.md.
        ok = await self._run_python_script(
            self.RECURRING_ID,
            ["scripts/recurring_runner.py"],
            log_filename="recurring.log",
        )
        if ok:
            await self._run_python_script(
                self.RECURRING_ID,
                ["scripts/render_portfolio.py", "--write"],
                log_filename="recurring.log",
                append=True,
            )

    async def _run_python_script(
        self,
        job_id: str,
        args: list[str],
        log_filename: str,
        append: bool = False,
    ) -> bool:
        """Run a Python script; record run state; return success bool."""
        state = self.jobs[job_id]
        run = JobRun(started_at=datetime.now(tz=IST).isoformat())
        state.last_run = run

        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOG_DIR / log_filename
        mode = "ab" if append else "wb"

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                *args,
                cwd=str(config.PROJECT_ROOT),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await proc.communicate()
            run.exit_code = proc.returncode
            with open(log_path, mode) as f:
                f.write(
                    f"\n=== {run.started_at} :: {' '.join(args)} (exit {proc.returncode}) ===\n".encode()
                )
                f.write(stdout)
            tail = stdout.decode("utf-8", errors="replace").strip().splitlines()[-20:]
            run.output_tail = "\n".join(tail)
            run.status = "success" if proc.returncode == 0 else "failed"
        except Exception as exc:
            logger.exception("Job %s failed", job_id)
            run.status = "failed"
            run.exit_code = None
            run.output_tail = f"Exception: {exc}"
        finally:
            run.finished_at = datetime.now(tz=IST).isoformat()
            state.history.append(run)
            # Cap history.
            state.history = state.history[-20:]

        return run.status == "success"


def _serialize_run(run: JobRun | None) -> dict[str, Any] | None:
    if run is None:
        return None
    return {
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "status": run.status,
        "exit_code": run.exit_code,
        "output_tail": run.output_tail,
    }


# Singleton — one scheduler per backend process.
service = Scheduler()
