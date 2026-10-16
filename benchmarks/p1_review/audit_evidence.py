#!/usr/bin/env python3
"""Recompute the P1 handoff from preserved logs; never modify source artifacts."""
import argparse
import hashlib
import json
import re
import statistics
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def seconds(value):
    result = 0.0
    for field in value.split(":"):
        result = result * 60 + float(field)
    return result


def timing(path):
    raw = path.read_text()
    log = ANSI.sub("", path.with_suffix(".log").read_text())
    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "log_sha256": hashlib.sha256(path.with_suffix(".log").read_bytes()).hexdigest(),
        "wall_s": seconds(re.search(r"Elapsed .*?:\s+([\d:.]+)", raw)[1]),
        "cpu_percent": float(re.search(r"Percent of CPU this job got:\s*(\d+)%", raw)[1]),
        "exit_status": int(re.search(r"Exit status:\s*(\d+)", raw)[1]),
        "solve_s": [float(x) for x in re.findall(r"Elapsed time\s*=\s*([\d.]+)s", log)][-2:],
        "kinetic_energy_printed": re.findall(r"Kinematic energy\s*=\s*(\S+)", log),
        "potential_energy_printed": re.findall(r"Potential energy\s*=\s*(\S+)", log),
        "iterations": [int(x) for x in re.findall(r"Total number of iterations\s*=\s*(\d+)", log)],
        "average_rebuild_interval_printed": [int(x) for x in re.findall(
            r"Average number of iterations between contact list updates\s*=\s*(\d+)", log)],
    }


def pair_summary(base, variant):
    b = [x["wall_s"] for x in base]
    v = [x["wall_s"] for x in variant]
    delta = [x-y for x, y in zip(b, v)]
    return {
        "baseline": base, "persistent": variant,
        "baseline_mean_s": statistics.mean(b), "persistent_mean_s": statistics.mean(v),
        "ratio_of_means": statistics.mean(b)/statistics.mean(v),
        "runtime_reduction_percent": 100*(1-statistics.mean(v)/statistics.mean(b)),
        "paired_delta_s": delta, "paired_delta_mean_s": statistics.mean(delta),
        "paired_delta_sd_s": statistics.stdev(delta),
        "all_paired_faster": all(x > 0 for x in delta),
        "printed_energies_equal_by_pair": [
            (x["kinetic_energy_printed"] == y["kinetic_energy_printed"] and
             x["potential_energy_printed"] == y["potential_energy_printed"])
            for x, y in zip(base, variant)],
        "solve_mean_baseline_s": statistics.mean(sum(x["solve_s"]) for x in base),
        "solve_mean_persistent_s": statistics.mean(sum(x["solve_s"]) for x in variant),
        "caution": "Printed energy equality is not a bitwise FP64 state comparison; CPU percent alone cannot prove contention.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = {"artifact_root": str(args.artifacts), "timings": {}, "oracle": {}}
    for size, prefix in [("small", "s"), ("large", "l")]:
        base = [timing(args.artifacts/"bench"/f"{prefix}base_rep{i}.time") for i in range(1, 6)]
        variant = [timing(args.artifacts/"bench"/f"{prefix}pers_rep{i}.time") for i in range(1, 6)]
        results["timings"][size] = pair_summary(base, variant)
    pattern = re.compile(r"DEM_ORACLE_STEP iter=(\d+) ref=(\d+) matched=(\d+) missing=(\d+) dup=(\d+)")
    for path in sorted((args.artifacts/"oracle").glob("logs_*.log")):
        rows = [[int(x) for x in match] for match in pattern.findall(path.read_text())]
        if not rows:
            raise RuntimeError(f"No oracle rows in {path}")
        results["oracle"][path.stem] = {
            "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "checks": len(rows), "reference_contacts": sum(x[1] for x in rows),
            "matched_contacts": sum(x[2] for x in rows),
            "missing_contacts": sum(x[3] for x in rows), "duplicates": sum(x[4] for x in rows),
        }
    results["oracle_totals"] = {key: sum(x[key] for x in results["oracle"].values())
        for key in ["checks", "reference_contacts", "matched_contacts", "missing_contacts", "duplicates"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2)+"\n")
    print(json.dumps({"timings": {k: {x: y for x, y in v.items() if x not in ["baseline", "persistent"]}
                                for k, v in results["timings"].items()},
                      "oracle": results["oracle"], "oracle_totals": results["oracle_totals"]}, indent=2))


if __name__ == "__main__":
    main()
