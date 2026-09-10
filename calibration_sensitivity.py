"""Measure input sensitivity; these samples do not replace saved reference rates."""

import argparse
import statistics
import time
from pathlib import Path
import benchmark
import validation
from experiments import load_inputs, save_json
from tspData import TspData
from tspFunctions import TspFunction


def measure(cases, duration=.25):
    rows = []
    for case in cases:
        matrix = case["matrix"]
        elapsed = 0.
        count = 0
        while elapsed < duration:
            tsp = TspData(len(matrix), matrix=matrix)
            start = time.perf_counter()
            nodes, _, _, _ = TspFunction.tsp_solver(tsp)
            elapsed += time.perf_counter() - start
            count += nodes
        tsp, transcript, sigma, root = benchmark._create_proof_benchmark_transcript(len(matrix), matrix)
        start = time.perf_counter()
        units = 0
        while time.perf_counter() - start < duration:
            assert validation._validate_proposed_tour(tsp, tsp.best_path, tsp.best_cost)
            assert validation._validate_transcript_root(tsp, transcript, sigma, root)
            valid, checked, _, _ = validation._validate_transcript_semantics(tsp, transcript, tsp.best_path, tsp.best_cost)
            assert valid
            units += benchmark._semantic_validation_units(transcript, checked)
        replay_elapsed = time.perf_counter() - start
        rows.append({"case_id": case["case_id"], "search_nodes_per_second": count / elapsed,
                     "semantic_units_per_second": units / replay_elapsed})
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="Saved paired experiment directory")
    args = parser.parse_args()
    directory = Path(args.directory)
    rows = measure(load_inputs(directory / "inputs.json")[:6])
    save_json(directory / "sensitivity.json", rows)
    print("Saved sensitivity measurements for", len(rows), "matrices")
