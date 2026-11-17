"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import math
from lab9.graders import GRADERS

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = []

    def inspect_report(report: dict, name: str) -> dict:
        rows = report.get("rows", [])
        manifest = report.get("manifest", {})
        seeds = manifest.get("seeds", [])

        if report.get("evaluator_failures"):
            problems.append(f"{name}: evaluator failures")

        for metric, value in report.get("metrics", {}).items():
            if value is None or (
                isinstance(value, (int, float))
                and not math.isfinite(value)
            ):
                problems.append(f"{name}: invalid metric {metric}")

        expected_count = manifest.get("items", 0) * len(seeds)
        if len(rows) != expected_count:
            problems.append(f"{name}: wrong row count")

        keys = [(row.get("item_id"), row.get("seed")) for row in rows]
        if len(keys) != len(set(keys)):
            problems.append(f"{name}: duplicate item/seed")

        graded = [
            metric["id"]
            for metric in spec.get("metrics", [])
            if metric["id"] in GRADERS
        ]
        for row in rows:
            for metric in graded:
                if row.get(metric) is None:
                    problems.append(f"{name}: missing row metric {metric}")
                    break

        return {key: row for key, row in zip(keys, rows)}

    pr_rows = inspect_report(pr, "PR")
    base_rows = inspect_report(base, "baseline")

    if set(pr_rows) != set(base_rows):
        problems.append("PR and baseline item/seed sets differ")
    else:
        for key in pr_rows:
            pr_slices = set(pr_rows[key].get("slices") or [])
            base_slices = set(base_rows[key].get("slices") or [])
            if pr_slices != base_slices:
                problems.append(f"slice tags differ for {key}")

    if base_spec and spec.get("eval_set_version") == base_spec.get("eval_set_version"):

        def check_rules(old_rules, new_rules, key_fn, kind):
            new_by_key = {key_fn(rule): rule for rule in new_rules}

            for old in old_rules:
                key = key_fn(old)
                new = new_by_key.get(key)

                if new is None:
                    problems.append(f"{kind} removed: {key}")
                    continue

                if old.get("blocking") and not new.get("blocking"):
                    problems.append(f"{kind} no longer blocking: {key}")

                old_threshold = old.get("threshold", old)
                new_threshold = new.get("threshold", new)

                if "min" in old_threshold:
                    if "min" not in new_threshold or new_threshold["min"] < old_threshold["min"]:
                        problems.append(f"{kind} minimum loosened: {key}")

                for upper in ("max", "max_increase"):
                    if upper in old_threshold:
                        if upper not in new_threshold or new_threshold[upper] > old_threshold[upper]:
                            problems.append(f"{kind} {upper} loosened: {key}")

                if old_threshold.get("no_significant_drop") and not new_threshold.get("no_significant_drop"):
                    problems.append(f"{kind} no_significant_drop removed: {key}")

        check_rules(
            base_spec.get("metrics", []),
            spec.get("metrics", []),
            lambda metric: metric["id"],
            "metric",
        )
        check_rules(
            base_spec.get("slices", []),
            spec.get("slices", []),
            lambda slice_spec: (slice_spec["name"], slice_spec["metric"]),
            "slice",
        )

    return problems



def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked = []
    lines = []
    bs = spec.get("bootstrap", {})

    for slice_spec in spec.get("slices", []):
        name = slice_spec["name"]
        metric = slice_spec["metric"]
        slice_id = f"slice:{name}/{metric}"

        pr_values = per_item(pr, metric, slice_name=name)
        base_values = per_item(base, metric, slice_name=name)

        failed = False
        note = ""

        if not pr_values or set(pr_values) != set(base_values):
            failed = True
            note = "missing or mismatched slice items"
        else:
            value = sum(pr_values.values()) / len(pr_values)
            note = f"value={value:.4f}"

            if "min" in slice_spec and value < slice_spec["min"]:
                failed = True

            if slice_spec.get("no_significant_drop"):
                keys = sorted(pr_values)
                delta, low, high = stats.paired_bootstrap(
                    [pr_values[k] for k in keys],
                    [base_values[k] for k in keys],
                    n_resamples=bs.get("n_resamples", 1000),
                    rng=bs.get("rng", 2027),
                    confidence=bs.get("confidence", 0.95),
                )
                note += f" Δ {delta:+.3f} CI [{low:+.3f}, {high:+.3f}]"
                if high < 0:
                    failed = True

        if failed and slice_spec.get("blocking"):
            blocked.append(slice_id)

        verdict = "BLOCK" if failed and slice_spec.get("blocking") else (
            "warn" if failed else "ok"
        )
        lines.append(f"  {slice_id:<36} {note} {verdict}")

    return blocked, lines   


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
