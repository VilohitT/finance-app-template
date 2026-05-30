"""
Forward projections — drift from a planned allocation, and goal-bucket corpus
trajectories.

These are deterministic models, not Monte Carlo. They use the principles.md §11
return scenarios (5%/5.5%/4% real for equity-heavy buckets) by default, but
return assumptions are caller-supplied so the helper is reusable for property
goal buckets, debt sleeves, etc.

`project_drift` answers: "if I execute this allocation plan and then maintain
sleeves at the new mix, where do I land in N months — and how does drift
look?"

`project_corpus` answers: "starting at corpus C, contributing M/month plus
known lumps, growing at R% real, do I hit goal G by year Y?"

Both helpers return base/optimistic/pessimistic scenarios when given a
ScenarioReturns triple, or a single scenario when given a scalar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


# Principles.md §11 default scenarios for equity-heavy long-horizon corpus
DEFAULT_REAL_RETURN_SCENARIOS = {
    "base": 0.05,
    "optimistic": 0.055,
    "pessimistic": 0.04,
}


@dataclass
class LumpReceipt:
    """A one-time inflow at a future date."""
    date: str   # ISO YYYY-MM-DD
    amount_inr: float


def project_drift(
    current_holdings: dict[str, float],
    flows: dict[str, float],
    months: int,
    sleeve_real_returns: dict[str, float] | None = None,
    hybrid_equity_weight: float = 0.65,
) -> dict:
    """
    Project where each sleeve lands in `months` months after applying `flows`.

    Args:
        current_holdings: ₹ per sleeve today, e.g. {"equity": 355250, ...}
        flows: ₹ to add per sleeve at month 0, e.g. output of optimal_sleeve_split
        months: months forward
        sleeve_real_returns: per-sleeve annual real returns (decimal, e.g. 0.05).
                             Defaults: equity=0.05, debt=0.015, gold=0.02, hybrid=0.04
        hybrid_equity_weight: see allocation.optimal_sleeve_split

    Returns:
        {
          "months": int,
          "sleeve_projections": {
            sleeve: {"start": ₹, "after_flow": ₹, "projected": ₹, "real_return": float}
          },
          "totals": {"start": ₹, "after_flow": ₹, "projected": ₹},
          "projected_pct": {sleeve: pct},
          "effective_equity_pct": float,
        }
    """
    defaults = {"equity": 0.05, "debt": 0.015, "gold": 0.02, "hybrid": 0.04}
    rets = {**defaults, **(sleeve_real_returns or {})}
    sleeves = sorted(set(current_holdings) | set(flows))

    sleeve_projections: dict[str, dict] = {}
    for s in sleeves:
        start = current_holdings.get(s, 0.0)
        after_flow = start + flows.get(s, 0.0)
        r = rets.get(s, 0.04)
        # Compound monthly: (1+r)^(months/12)
        proj = after_flow * ((1 + r) ** (months / 12))
        sleeve_projections[s] = {
            "start": round(start, 2),
            "after_flow": round(after_flow, 2),
            "projected": round(proj, 2),
            "real_return": r,
        }

    total_start = sum(p["start"] for p in sleeve_projections.values())
    total_after_flow = sum(p["after_flow"] for p in sleeve_projections.values())
    total_proj = sum(p["projected"] for p in sleeve_projections.values())
    pct = {
        s: round(p["projected"] / total_proj, 4) if total_proj > 0 else 0.0
        for s, p in sleeve_projections.items()
    }
    eff_eq = (
        sleeve_projections.get("equity", {}).get("projected", 0.0)
        + hybrid_equity_weight * sleeve_projections.get("hybrid", {}).get("projected", 0.0)
    )
    eff_eq_pct = (eff_eq / total_proj) if total_proj > 0 else 0.0

    return {
        "months": months,
        "sleeve_projections": sleeve_projections,
        "totals": {
            "start": round(total_start, 2),
            "after_flow": round(total_after_flow, 2),
            "projected": round(total_proj, 2),
        },
        "projected_pct": pct,
        "effective_equity_pct": round(eff_eq_pct, 4),
    }


def _months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def project_corpus(
    start_value_inr: float,
    monthly_flow_inr: float,
    target_date: str,
    real_return_pct: float | dict[str, float] = DEFAULT_REAL_RETURN_SCENARIOS,
    lump_schedule: list[LumpReceipt] | None = None,
    today: str | None = None,
) -> dict:
    """
    Project corpus from `today` (or `start`) to `target_date`.

    Compounds monthly:
        each month: corpus = corpus * (1 + r/12) + monthly_flow
    Lumps in `lump_schedule` are added on the month they arrive.

    If `real_return_pct` is a dict (scenarios), runs each scenario.

    Returns:
        {
          "start_date": str, "target_date": str, "months": int,
          "scenarios": {scenario_name: {"final_corpus_inr": ₹, "real_return": float}},
          "single_scenario": ₹ | None       # populated when real_return_pct is scalar
        }
    """
    start_d = date.fromisoformat(today) if today else date.today()
    end_d = date.fromisoformat(target_date)
    months = _months_between(start_d, end_d)
    if months <= 0:
        raise ValueError(f"target_date {target_date} must be after today {start_d}")

    lumps = lump_schedule or []
    lump_by_month: dict[int, float] = {}
    for L in lumps:
        ld = date.fromisoformat(L.date)
        m = _months_between(start_d, ld)
        if 0 <= m < months:
            lump_by_month[m] = lump_by_month.get(m, 0.0) + L.amount_inr

    def run(r: float) -> float:
        corpus = start_value_inr
        monthly_r = r / 12.0
        for m in range(months):
            corpus = corpus * (1 + monthly_r) + monthly_flow_inr + lump_by_month.get(m, 0.0)
        return corpus

    if isinstance(real_return_pct, dict):
        scenarios = {
            name: {"final_corpus_inr": round(run(r), 2), "real_return": r}
            for name, r in real_return_pct.items()
        }
        single = None
    else:
        scenarios = {"single": {"final_corpus_inr": round(run(real_return_pct), 2),
                                "real_return": real_return_pct}}
        single = scenarios["single"]["final_corpus_inr"]

    return {
        "start_date": start_d.isoformat(),
        "target_date": target_date,
        "months": months,
        "scenarios": scenarios,
        "single_scenario": single,
    }


def goal_progress(
    current_corpus_inr: float,
    target_corpus_inr: float,
    target_date: str,
    monthly_flow_inr: float,
    real_return_pct: float | dict[str, float] = DEFAULT_REAL_RETURN_SCENARIOS,
    lump_schedule: list[LumpReceipt] | None = None,
    today: str | None = None,
) -> dict:
    """
    Convenience wrapper: projects corpus and reports % of goal achieved per scenario.
    """
    proj = project_corpus(
        current_corpus_inr, monthly_flow_inr, target_date, real_return_pct,
        lump_schedule, today,
    )
    progress = {
        name: {
            **info,
            "pct_of_target": round(info["final_corpus_inr"] / target_corpus_inr, 4)
                              if target_corpus_inr > 0 else 0.0,
            "shortfall_inr": round(target_corpus_inr - info["final_corpus_inr"], 2),
        }
        for name, info in proj["scenarios"].items()
    }
    return {
        **proj,
        "target_corpus_inr": target_corpus_inr,
        "scenarios": progress,
    }
