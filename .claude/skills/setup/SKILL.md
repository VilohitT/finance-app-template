---
name: setup
description: One-shot first-run installer for the finance-app template. Verifies Python prerequisites, bootstraps the NAV data layer, optionally installs the daily NAV refresh cron job (macOS launchd / Linux cron), confirms all foundation file scaffolds exist, and points the user to /finance-grill as the next step. Use whenever a new user has just cloned this template and is opening it for the first time, or whenever they say "set this up" / "install" / "what do I do first". Idempotent — safe to re-run if the user wants to revisit the cron install or confirm everything still works. Indian-context aware (AMFI NAV source, IST timezone for cron).
---

# setup

A one-shot first-run installer. Runs the mechanical setup steps a new user would otherwise have to discover themselves: Python prereqs, data layer bootstrap, optional daily NAV refresh job, scaffold verification.

## When to use

Trigger this skill when:

- The user has just cloned this template and is opening it for the first time
- They say "set this up" / "install" / "what do I do first" / "get me started"
- They want to re-verify the install (e.g., after moving the project, switching machines, restoring from backup)
- A skill flagged a setup issue (e.g., `discover.py` reported a STALE NAV layer and no daily cron is installed)

This is **idempotent** — re-running is safe. Steps that have already been completed are detected and skipped.

## What this skill does NOT do

- **Does not populate `goals.md`, `user-principles.md`, or `portfolio.md`.** Those are filled by `/finance-grill`, `/principles-grill`, and `/portfolio-grill` respectively. Setup confirms the scaffolds exist; the grills fill them.
- **Does not install Python.** If Python 3 isn't on the system, setup tells the user how to install it and stops.
- **Does not modify `principles.md` or `laws/`.** Those ship populated with the template.
- **Does not push or pull anything to/from a remote.** Local-first by design.

## What this skill produces

A confirmed working install:
- Python 3 + `requests` available
- `data/market.db` schemes table populated; today's NAVs fetched
- (Optional, user choice) macOS launchd plist installed for daily NAV refresh, OR Linux cron line added, OR Windows manual instructions printed
- All foundation file scaffolds present (`goals.md`, `principles.md`, `user-principles.md`, `portfolio.md`, `decisions-log.md`)

And a clear next-step message: "run `/finance-grill` to capture your financial situation."

## Workflow

### Step 1 — Verify Python and required packages

```bash
python3 --version
python3 -c "import sys; assert sys.version_info >= (3, 10), 'Python 3.10+ required'; print('OK')"
python3 -c "import requests; print(f'requests {requests.__version__}')"
python3 -c "import sqlite3; print(f'sqlite3 {sqlite3.sqlite_version}')"
```

If any of these fail, tell the user:
- Python 3.10+ needed: install via Homebrew (`brew install python`), apt (`sudo apt install python3`), or python.org installer
- `requests` missing: `pip3 install requests` (or `pip3 install --user requests`)
- `sqlite3` should be in the stdlib; if missing, the Python install is broken

Stop and ask the user to resolve before proceeding.

### Step 2 — Inspect data layer

Check `data/market.db`:

```bash
sqlite3 data/market.db "SELECT 'schemes:', COUNT(*) FROM schemes; SELECT 'nav_history:', COUNT(*) FROM nav_history; SELECT 'fetch_log:', COUNT(*) FROM fetch_log;"
```

Expected on first run (template ships pre-seeded):
- `schemes: ~14000` ✓
- `nav_history: 0`  (will be populated by the first fetch)
- `fetch_log: 0`

If `schemes: 0` (template ship was incomplete or DB got reset), proceed to Step 3 — the first `fetch_nav.py` run will populate both `schemes` and today's `nav_history`.

If `nav_history: > 0` already, the user has run setup before; tell them and offer to skip to Step 4.

### Step 3 — Bootstrap NAVs

Run the daily NAV fetcher once to populate today's NAVs across all ~14,000 schemes:

```bash
python3 scripts/fetch_nav.py --quiet
```

This typically takes 30-60 seconds. After completion, verify:

```bash
sqlite3 data/market.db "SELECT COUNT(*) FROM nav_history;"
sqlite3 data/market.db "SELECT source, fetch_time, status, record_count FROM fetch_log ORDER BY fetch_time DESC LIMIT 1;"
```

Expected: `nav_history` count jumps to ~14,000; `fetch_log` shows one successful row.

If the fetch fails (network error, AMFI down), tell the user, recommend retrying, and continue without blocking.

### Step 4 — Detect platform and offer daily cron

```bash
uname -s
```

Branch:

**macOS (`Darwin`)** — offer to install the launchd plist:

> "I can install a daily NAV refresh job that runs at 22:30 local time. This keeps your portfolio review's drift figures current without you having to remember.
>
> Want me to set it up? [yes / skip]"

If yes:

1. Detect the absolute project root:
   ```bash
   pwd
   ```
2. Edit `scripts/com.template.financeapp.fetchnav.plist` to replace `{{PROJECT_ROOT}}` with the absolute path, and edit the Label's `yourusername` to something unique on the machine (use `$USER` from env). Write the edited file to `~/Library/LaunchAgents/com.<username>.financeapp.fetchnav.plist`.
3. Ensure log directory exists:
   ```bash
   mkdir -p data/logs
   ```
4. Load it:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.<username>.financeapp.fetchnav.plist
   launchctl list | grep financeapp
   ```
5. Confirm: the list output should show the label. Tell the user.

Repeat for `scripts/com.template.financeapp.recurring.plist` (monthly recurring tranche generator) — but ask first if the user expects to register SIPs/STPs; if not, defer this until they do.

**Linux** — offer to install a cron line:

> "I can add two cron lines: daily NAV refresh (22:30) and monthly recurring tranche generation (6th, 08:00). Want me to set them up? [yes / skip]"

If yes:
1. Detect project root and substitute into `scripts/cron-template.txt`.
2. Append the two lines to the user's crontab via `(crontab -l 2>/dev/null; cat scripts/cron-template-resolved.txt) | crontab -`.
3. Verify: `crontab -l | grep financeapp`.

**Windows** — print manual instructions:

> "Windows Task Scheduler can run these jobs. The two commands to schedule:
>
> Daily NAV refresh (22:30):
>   `python3 {{PROJECT_ROOT}}\scripts\fetch_nav.py --quiet`
>
> Monthly recurring (6th, 08:00):
>   `python3 {{PROJECT_ROOT}}\scripts\recurring_runner.py && python3 {{PROJECT_ROOT}}\scripts\render_portfolio.py --write`
>
> Open Task Scheduler → Create Basic Task → set the trigger and action. Or run them manually whenever you remember."

### Step 5 — Verify all foundation file scaffolds exist

```bash
for f in goals.md principles.md user-principles.md portfolio.md decisions-log.md; do
  [ -f "$f" ] && echo "✓ $f" || echo "✗ MISSING: $f"
done
```

If any are missing (shouldn't happen on a fresh template clone), report which and ask the user to confirm they want the skill to recreate the scaffolds.

### Step 6 — Summary and next step

Output a clean summary:

```
✓ Python 3.X.X + requests + sqlite3
✓ data/market.db: 14,372 schemes, today's NAVs loaded
✓ Daily NAV refresh: installed (macOS launchd / Linux cron / skipped)
✓ Foundation scaffolds present: goals.md, principles.md, user-principles.md, portfolio.md, decisions-log.md

Next step: run `/finance-grill` to capture your financial situation (~30 min interview).
After that:
  - `/principles-grill` → captures your investment structure (sleeve targets, routing) (~10 min)
  - `/portfolio-grill` → captures every holding (~20-40 min)
  - `/portfolio-review` → your weekly check-in once everything's set up

See GETTING_STARTED.md for the full Day-1 walkthrough.
```

## Key reminders

- **Idempotent.** Detect existing state at every step; don't re-run completed work.
- **Network-dependent.** Step 3 (NAV bootstrap) needs internet. If offline, defer and proceed.
- **No silent installs.** Always ask before loading a launchd job or adding a cron line — these run automatically and the user should consent.
- **Don't populate the grills' files.** Setup only confirms scaffolds exist; the grills fill them.
- **Platform branching.** macOS / Linux / Windows each have their own daily-job mechanism; the skill detects and routes accordingly.
- **Path absolutisation matters.** All cron/launchd configs need absolute paths. Use `pwd` to capture, and substitute into the template files before loading.
