"""Paired, replayable experiments with raw data and fixed reference calibration.

Run: python experiments.py --output experiment-output --runs 40 --cities 12
Replay: python experiments.py --replay experiment-output --output repeated-output
"""

import argparse
import copy
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import sys
import time

import benchmark
from mainFunctions import MainFunctions as Main
from hostRuntime import cancellation, check_cancelled
from nodes import Node

MODES = {0: "none", 1: "proof", 2: "council"}
COMPONENTS = ["search_compute_work", "transcript_compute_work",
              "proof_hash_compute_work", "proof_semantic_compute_work",
              "council_initial_compute_work", "council_branch_compute_work"]


def make_inputs(seed, runs, cities, workers):
    """Generate explicit paired inputs using the simulation's edge distribution."""
    rng = random.Random(seed)
    cases = []
    for index in range(runs):
        matrix = [[math.inf] * cities for _ in range(cities)]
        for i in range(cities):
            for j in range(i + 1, cities):
                decimal = 10 ** rng.randint(1, 2)
                value = rng.randint(1, 9) * decimal
                if decimal == 100 and rng.randint(1, 4) == 1:
                    value += rng.randint(1, 9) * 10
                matrix[i][j] = matrix[j][i] = value
        cases.append({
            "case_id": index, "matrix": matrix,
            "workers": [{"hash_rate": rng.randint(100, 1000),
                         "reward": rng.randbytes(10).hex()} for _ in range(workers)],
            "block": {"previous_hash": rng.randbytes(32).hex(),
                      "timestamp": "2000-01-01 00:00:00",
                      "transactions": [rng.randbytes(10).hex() for _ in range(10)]},
            "sigma": rng.randbytes(32).hex(),
        })
    return cases


def clean_json(value):
    """Encode unavailable matrix edges as JSON null, avoiding nonstandard Infinity."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    return value


def save_json(path, value):
    Path(path).write_text(json.dumps(clean_json(value), indent=2, allow_nan=False), encoding="utf-8")


def load_inputs(path):
    cases = json.loads(Path(path).read_text(encoding="utf-8"))
    for case in cases:
        case["matrix"] = [[math.inf if v is None else v for v in row] for row in case["matrix"]]
    return cases


def calibrate(cities, repetitions=1, duration=2.0):
    """Measure all seven rates once for use by every paired variant."""
    functions = [benchmark.benchmark_pow, benchmark.benchmark_tsp_pouw,
                 benchmark.benchmark_initial_validation, benchmark.benchmark_branch_validation,
                 benchmark.benchmark_transcript, benchmark.benchmark_hash_validation,
                 benchmark.benchmark_semantic_validation]
    samples = {}
    for name, function in zip(Main.rate_names(), functions):
        samples[name] = [function(duration=duration, **({} if index == 0 else {"size": cities}))
                         for index in [functions.index(function)] for _ in range(repetitions)]
        check_cancelled()
    return {key: statistics.mean(values) for key, values in samples.items()}, samples


def summary(values):
    """Mean, sample SD and percentile bootstrap CI over independent input cases.

    This interval covers input variability conditional on saved calibration; it
    does not estimate reference-rate uncertainty or blockchain security.
    """
    rng = random.Random(20260910)
    n = len(values)
    if n < 2:
        return {"n": n, "mean": statistics.mean(values), "sd": None, "ci95": None}
    means = sorted(statistics.mean(rng.choices(values, k=n)) for _ in range(2000))
    return {"n": n, "mean": statistics.mean(values), "sd": statistics.stdev(values),
            "ci95": [means[49], means[1949]]}


def source_manifest():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(__file__).parent.glob("*.py"))}


def run_experiment(cases, rates, difficulty, workers, output):
    """Run PoW once per case, and reuse matrix/capabilities across all TSP modes."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    save_json(output / "inputs.json", cases)
    save_json(output / "calibration.json", rates)
    rows = []
    for case in cases:
        for mode in MODES:
            check_cancelled()
            model = Main(len(case["workers"]), len(case["matrix"]), 1, difficulty, mode,
                         host_workers=workers, calibration=rates, run_inputs=[case])
            model.reset_simulation()
            if mode == 0:
                start = time.perf_counter()
                result = model.multiple_node_pow(difficulty)
                rows.append({"case_id": case["case_id"], "mode": "pow",
                             "host_wall_seconds": time.perf_counter() - start, **result})
                model.reset_simulation()
            start = time.perf_counter()
            result = model.multiple_node_pouw_tsp()
            if not result["validation_valid"]:
                raise RuntimeError("Rejected proposal; no successful experiment summary written")
            rows.append({"case_id": case["case_id"], "mode": MODES[mode],
                         "host_wall_seconds": time.perf_counter() - start, **result})
        # Preserve progress if a later case is cancelled or fails.
        save_json(output / "runs.json", rows)
    fields = sorted({key for row in rows for key, value in row.items()
                     if not isinstance(value, (dict, list))})
    with (output / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    stats = {}
    for mode in ["pow", *MODES.values()]:
        selected = [r for r in rows if r["mode"] == mode]
        keys = ["compute_work", "simulation_time"] if mode == "pow" else ["total_compute_work", "total_time", *COMPONENTS]
        stats[mode] = {key: summary([r[key] for r in selected]) for key in keys}
    baseline = {r["case_id"]: r for r in rows if r["mode"] == "none"}
    for mode in ["proof", "council"]:
        selected = [r for r in rows if r["mode"] == mode]
        stats[mode + "_paired_extra"] = {
            key: summary([r[key] - baseline[r["case_id"]][key] for r in selected])
            for key in ["total_compute_work", "total_time"]}
    save_json(output / "summary.json", stats)
    return stats


def export_plots(stats, output):
    """Export publication figures from saved statistics, without GUI screenshots."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output = Path(output)
    labels = ["PoW", "PoUW", "Proof", "Council"]
    for metric, filename, ylabel in [("work", "paired_work", "Referentni računalni rad [s]"),
                                      ("time", "paired_time", "Simulirano vrijeme [s]")]:
        items = [stats[m][("compute_work" if metric == "work" else "simulation_time") if m == "pow"
                          else ("total_compute_work" if metric == "work" else "total_time")]
                 for m in ["pow", "none", "proof", "council"]]
        means = [s["mean"] for s in items]
        errors = [[s["mean"] - s["ci95"][0] if s["ci95"] else 0 for s in items],
                  [s["ci95"][1] - s["mean"] if s["ci95"] else 0 for s in items]]
        fig, ax = plt.subplots(figsize=(6.2, 3.4), layout="constrained")
        ax.bar(labels, means, yerr=errors, capsize=4, color=["#65748b", "#2979a5", "#da9633", "#55976b"])
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=.2)
        ax.set_axisbelow(True)
        fig.savefig(output / (filename + ".pdf"))
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(6.8, 3.8), layout="constrained")
    bottom = [0., 0., 0.]
    names = ["Pretraživanje", "Zapis transkripta", "Hash provjere", "Semantički replay", "Council: obilazak", "Council: grane"]
    for key, label in zip(COMPONENTS, names):
        values = [stats[m][key]["mean"] for m in MODES.values()]
        ax.bar(["Bez validacije", "Proof", "Council"], values, bottom=bottom, label=label)
        bottom = [a+b for a,b in zip(bottom, values)]
    ax.set_ylabel("Referentni računalni rad [s]")
    ax.set_ylim(0, max(bottom) * 1.12)
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1, 1))
    fig.savefig(output / "paired_components.pdf")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="experiment-output")
    parser.add_argument("--replay", help="Reuse saved inputs, calibration and difficulty")
    parser.add_argument("--runs", type=int, default=40)
    parser.add_argument("--cities", type=int, default=12)
    parser.add_argument("--nodes", type=int, default=5)
    parser.add_argument("--difficulty", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260910)
    parser.add_argument("--host-workers", type=int, default=1)
    parser.add_argument("--benchmark-runs", type=int, default=1)
    parser.add_argument("--cpu-percent", type=int)
    args = parser.parse_args()
    if min(args.runs, args.host_workers, args.benchmark_runs) < 1 or args.cities < 3 or args.nodes < 3 or not 1 <= args.difficulty <= 8:
        parser.error("Invalid experiment dimensions or host settings")
    if args.cpu_percent is not None:
        from windowsCpuLimit import apply_cpu_limit
        apply_cpu_limit(args.cpu_percent)
    output = Path(args.output)
    if output.exists() and any(output.iterdir()):
        parser.error("Use an empty output directory to preserve earlier experiment evidence")
    output.mkdir(parents=True, exist_ok=True)
    if args.replay:
        source = Path(args.replay)
        cases = load_inputs(source / "inputs.json")
        rates = json.loads((source / "calibration.json").read_text())
        args.difficulty = json.loads((source / "metadata.json").read_text())["difficulty"]
        samples = None
    else:
        cases = make_inputs(args.seed, args.runs, args.cities, args.nodes)
        rates, samples = calibrate(args.cities, args.benchmark_runs)
    save_json(output / "calibration_samples.json", samples)
    save_json(output / "metadata.json", {
        "python": sys.version, "platform": platform.platform(),
        "cpu_model": platform.processor(), "logical_cpus": os.cpu_count(),
        "affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
        "host_workers": args.host_workers, "cpu_percent": args.cpu_percent,
        "difficulty": args.difficulty, "seed": args.seed if not args.replay else None,
        "replay_of": args.replay, "source_sha256": source_manifest(),
        "benchmark_duration_target": 2.0, "benchmark_repetitions": args.benchmark_runs if not args.replay else None,
    })
    stats = run_experiment(cases, rates, args.difficulty, args.host_workers, output)
    export_plots(stats, output)
    print(f"Saved {len(cases)} paired cases to {output}")
