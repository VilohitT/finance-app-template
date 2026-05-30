"""
Allocation arithmetic — drives a sub-portfolio toward target sleeve weights
using flows only, never sales (principle 6.3).

Core function: optimal_sleeve_split(current, targets, new_money, ...)
- Returns the per-sleeve ₹ split for `new_money` that maximally closes the gap
  to `targets`, subject to constraints:
    - Zero flow into over-allocated sleeves (principle 6.3)
    - Zero flow into excluded sleeves (e.g. user said "no PPF")
    - Hybrid holdings can be counted as fractional equity for tax-treatment-aware
      drift (default 65% equity weight, since equity-oriented hybrids carry
      ≥65% equity per SEBI rules)
- Also returns projected post-deployment sleeve mix.

Sleeves are user-defined keys; common values: "equity", "debt", "gold", "hybrid".
The function is sleeve-agnostic — you pass a dict, it returns a dict.
"""

from __future__ import annotations


def _project(
    current: dict[str, float],
    flows: dict[str, float],
    hybrid_equity_weight: float = 0.65,
) -> dict:
    """Project the post-deployment sleeve mix and tax-aware effective equity."""
    after = {k: current.get(k, 0.0) + flows.get(k, 0.0) for k in set(current) | set(flows)}
    total = sum(after.values())
    pct = {k: (v / total if total > 0 else 0.0) for k, v in after.items()}
    eff_equity = (
        after.get("equity", 0.0) + hybrid_equity_weight * after.get("hybrid", 0.0)
    )
    eff_equity_pct = (eff_equity / total) if total > 0 else 0.0
    return {
        "after_inr": {k: round(v, 2) for k, v in after.items()},
        "after_pct": {k: round(v, 4) for k, v in pct.items()},
        "effective_equity_inr": round(eff_equity, 2),
        "effective_equity_pct": round(eff_equity_pct, 4),
        "total_inr": round(total, 2),
    }


def optimal_sleeve_split(
    current: dict[str, float],
    targets: dict[str, float],
    new_money: float,
    exclude_sleeves: set[str] | None = None,
    hybrid_equity_weight: float = 0.65,
    minimum_floor_inr: float = 0.0,
) -> dict:
    """
    Compute per-sleeve ₹ split for `new_money`.

    Args:
        current: ₹ currently in each sleeve, e.g. {"equity": 355250, "debt": 1148000, "gold": 0, "hybrid": 200000}
        targets: target % per sleeve as decimals, e.g. {"equity": 0.65, "debt": 0.30, "gold": 0.05}
                 Sleeves omitted from `targets` get target 0%.
        new_money: ₹ to allocate
        exclude_sleeves: set of sleeve names that get zero flow regardless of drift.
                         Common: {"ppf"} when user opts out, {"hybrid"} if no target.
        hybrid_equity_weight: how much of "hybrid" counts toward "equity" for the
                              effective-equity drift calculation. Defaults to 0.65
                              (SEBI's threshold for equity-oriented hybrid).
        minimum_floor_inr: if a sleeve has a positive gap, give it at least this
                           much. Useful to ensure tiny but non-zero gold flow
                           when opening a new sleeve.

    Returns:
        {
          "flows": {sleeve: ₹},                # per-sleeve flow (sums to new_money)
          "rationale": {sleeve: str},          # short reason per sleeve
          "post_deployment": {                  # see _project()
            "after_inr": {...}, "after_pct": {...},
            "effective_equity_inr": float, "effective_equity_pct": float,
            "total_inr": float,
          },
          "remaining_gap_to_target": {sleeve: ₹}  # how much more flow needed to hit target after this round
        }

    Raises:
        ValueError if new_money < 0 or targets don't sum to ~1.0.
    """
    if new_money < 0:
        raise ValueError(f"new_money must be non-negative, got {new_money}")
    excluded = exclude_sleeves or set()
    target_sum = sum(targets.values())
    if not (0.99 <= target_sum <= 1.01):
        raise ValueError(f"targets must sum to ~1.0, got {target_sum:.4f}")
    # Reject the degenerate "everything excluded" case so new_money cannot be
    # silently dropped. Caller must drop a sleeve from exclude_sleeves or pass
    # new_money=0 if they truly want a no-op.
    if new_money > 0:
        all_keys = set(current) | set(targets)
        if all_keys and excluded.issuperset(all_keys):
            raise ValueError(
                "all sleeves excluded; cannot place new_money. "
                "Drop a sleeve from exclude_sleeves or pass new_money=0."
            )

    sleeves = sorted(set(current) | set(targets))
    total_now = sum(current.get(k, 0.0) for k in sleeves)
    total_after = total_now + new_money
    rationale: dict[str, str] = {}

    # 1. Compute the ideal post-deployment ₹ for each sleeve
    ideal_after = {k: targets.get(k, 0.0) * total_after for k in sleeves}

    # 2. Compute the gap (positive = under-allocated, needs flow)
    gap = {k: ideal_after[k] - current.get(k, 0.0) for k in sleeves}

    # 3. Zero out gaps for excluded or over-allocated sleeves
    for k in sleeves:
        if k in excluded:
            gap[k] = 0.0
            rationale[k] = "excluded by caller"
        elif gap[k] <= 0:
            gap[k] = 0.0
            if targets.get(k, 0.0) == 0.0:
                rationale[k] = "no target (sleeve being amortised by drift)"
            else:
                rationale[k] = "over-allocated; no flow per principle 6.3"

    # 4. Effective minimum floor per sleeve, capped at the sleeve's own gap so
    #    we never over-allocate past target. Sleeves with gap<=0 (excluded or
    #    over-allocated) get a 0 floor.
    if minimum_floor_inr > 0:
        effective_floor = {
            k: (min(minimum_floor_inr, gap[k]) if gap[k] > 0 else 0.0)
            for k in sleeves
        }
    else:
        effective_floor = {k: 0.0 for k in sleeves}
    floor_total = sum(effective_floor.values())

    # 5. Distribute new_money.
    total_gap = sum(gap.values())
    flows: dict[str, float] = {}
    if total_gap <= 0:
        # Nothing under-allocated (or everything excluded). Park residual in the
        # least-over-allocated sleeve that isn't excluded.
        for k in sleeves:
            flows[k] = 0.0
        candidates = [k for k in sleeves if k not in excluded]
        if candidates:
            # Pick sleeve with largest target (most-aligned-with-policy fallback)
            fallback = max(candidates, key=lambda k: targets.get(k, 0.0))
            flows[fallback] = new_money
            rationale[fallback] = (
                rationale.get(fallback, "")
                + " | residual parked here (no under-allocation)"
            ).strip(" |")
    elif floor_total >= new_money and floor_total > 0:
        # Tight money — can't fund all floors. Pro-rata new_money to the floors
        # themselves so every under-funded sleeve gets a fractional floor share
        # rather than zero.
        for k in sleeves:
            flows[k] = (
                round(new_money * effective_floor[k] / floor_total, 2)
                if effective_floor[k] > 0 else 0.0
            )
            if flows[k] > 0:
                pct = (effective_floor[k] / floor_total) * 100
                rationale[k] = (
                    f"under-allocated; {pct:.1f}% of new money "
                    "(pro-rata to floor — money below total floor)"
                )
        diff = round(new_money - sum(flows.values()), 2)
        if abs(diff) >= 0.005:
            top = max(flows, key=flows.get)
            flows[top] = round(flows[top] + diff, 2)
    elif total_gap >= new_money:
        # Reserve each sleeve's floor, then pro-rata the remainder by residual
        # gap. This keeps the floor an actual floor.
        remaining = new_money - floor_total
        residual_gap = {k: max(0.0, gap[k] - effective_floor[k]) for k in sleeves}
        total_residual = sum(residual_gap.values())
        for k in sleeves:
            bonus = (
                round(remaining * residual_gap[k] / total_residual, 2)
                if residual_gap[k] > 0 and total_residual > 0 else 0.0
            )
            flows[k] = round(effective_floor[k] + bonus, 2)
            if flows[k] > 0:
                pct = (gap[k] / total_gap) * 100
                rationale[k] = f"under-allocated; {pct:.1f}% of new money (pro-rata to gap)"
        # Fix rounding drift so flows sum exactly to new_money
        diff = round(new_money - sum(flows.values()), 2)
        if abs(diff) >= 0.005:
            top = max(flows, key=flows.get)
            flows[top] = round(flows[top] + diff, 2)
    else:
        # Available money exceeds total gap → fill all gaps, distribute surplus
        # to the largest-target sleeve that wasn't excluded.
        for k in sleeves:
            flows[k] = round(gap[k], 2) if gap[k] > 0 else 0.0
            if flows[k] > 0:
                rationale[k] = f"under-allocated; gap fully filled"
        surplus = round(new_money - sum(flows.values()), 2)
        if surplus > 0:
            candidates = [k for k in sleeves if k not in excluded and targets.get(k, 0.0) > 0]
            if candidates:
                target_dest = max(candidates, key=lambda k: targets.get(k, 0.0))
                flows[target_dest] = round(flows[target_dest] + surplus, 2)
                rationale[target_dest] += " | + surplus parked here"

    # 6. Compute remaining gap after this round
    remaining = {
        k: max(0.0, round(gap[k] - flows.get(k, 0.0), 2)) for k in sleeves
    }

    # 7. Project post-deployment mix
    post = _project(current, flows, hybrid_equity_weight)

    return {
        "flows": {k: v for k, v in flows.items() if v != 0 or k in current or k in targets},
        "rationale": rationale,
        "post_deployment": post,
        "remaining_gap_to_target": remaining,
    }
