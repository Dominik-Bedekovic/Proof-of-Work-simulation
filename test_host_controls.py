"""Verify bounded execution without weakening logical work or certificate checks."""

import copy
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import benchmark
import validation
from experiments import make_inputs, load_inputs, save_json
from hostRuntime import HostPool, SimulationCancelled, cancellation
from mainFunctions import MainFunctions as Main
from test_regressions import cached_main, proof_for, MATRIX


def fail_worker(value):
    raise ValueError("intentional worker failure")


def stalled_worker(value):
    time.sleep(5)
    return value


def lost_worker(value):
    os._exit(1)


class HostControls(unittest.TestCase):
    def test_limits(self):
        for value in [0, -1, True, 1.5]:
            with self.assertRaises(ValueError):
                HostPool(value)
        with patch("hostRuntime.mp.get_context", side_effect=AssertionError("unexpected process")):
            with HostPool(1) as pool:
                self.assertEqual(pool.map(abs, [-1, -2]), [1, 2])
                self.assertEqual(pool.map(abs, []), [])

    def test_spawn_and_order(self):
        with HostPool(2) as pool:
            self.assertEqual(pool.map(abs, [-3, -1, -2]), [3, 1, 2])
            self.assertLessEqual(len(pool.pool._pool), 2)

    def test_worker_failure(self):
        with self.assertRaisesRegex(ValueError, "intentional"):
            with HostPool(2) as pool:
                pool.map(fail_worker, [1, 2])

    def test_lost_worker_timeout(self):
        with self.assertRaises(TimeoutError):
            with HostPool(2, timeout=.5) as pool:
                pool.map(lost_worker, [1])

    def test_cancel_pool_and_calibration(self):
        for function in [lambda: benchmark.benchmark_pow(duration=5), self.block_in_pool]:
            event = threading.Event()
            timer = threading.Timer(.1, event.set)
            timer.start()
            start = time.monotonic()
            try:
                with self.assertRaises(SimulationCancelled), cancellation(event):
                    function()
                self.assertLess(time.monotonic() - start, 3)
            finally:
                timer.cancel()

    @staticmethod
    def block_in_pool():
        with HostPool(2) as pool:
            pool.map(stalled_worker, [1, 2])

    def test_paused_replay_cancels(self):
        tsp, path, cost, transcript, validators, sigma, root = proof_for(MATRIX)
        event = threading.Event()
        with cancellation(event):
            event.set()
            with self.assertRaises(SimulationCancelled):
                validation._validate_transcript_semantics(tsp, transcript, path, cost)

    def test_hash_slice_offsets_and_boundaries(self):
        tsp, path, cost, transcript, validators, sigma, root = proof_for(MATRIX)
        serial = validation._parallel_hash_validation(transcript, validators, root, 1, 0)
        parallel = validation._parallel_hash_validation(transcript, validators, root, 2, 0)
        self.assertEqual(serial, parallel)
        n = len(transcript.steps)
        for index in [0, n // 2, n - 1]:
            changed = copy.deepcopy(transcript)
            changed.steps[index]["previous_hash"] = "bad boundary"
            self.assertFalse(validation._parallel_hash_validation(changed, validators, root, 2, 0)[0])
        sliced = transcript.steps[2:5]
        args = (0, sliced, 2, transcript.steps[1]["hash"])
        self.assertTrue(validation._hash_slice_worker(args)[1])
        self.assertFalse(validation._hash_slice_worker((0, sliced, 0, args[-1]))[1])

    def test_saved_input_roundtrip(self):
        cases = make_inputs(4, 2, 5, 3)
        self.assertEqual(cases, make_inputs(4, 2, 5, 3))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inputs.json"
            save_json(path, cases)
            self.assertNotIn("Infinity", path.read_text())
            self.assertEqual(load_inputs(path), cases)

    def test_same_simulation_for_one_and_two_host_workers(self):
        cached_main()
        rates = {name: getattr(Main, name) for name in Main.rate_names()}
        cases = make_inputs(42, 2, 5, 3)
        for mode in [0, 1, 2]:
            results = []
            for workers in [1, 2]:
                m = Main(3, 5, 2, 1, mode, host_workers=workers, calibration=rates, run_inputs=cases)
                results.append(m.run_simulation())
            self.assertEqual(results[0], results[1])

    def test_no_gui_import_in_entry_module(self):
        # A clean child interpreter must not load Matplotlib when importing main.
        import subprocess, sys
        result = subprocess.run([sys.executable, "-c", "import main,sys; assert 'gui' not in sys.modules; assert 'matplotlib' not in sys.modules"], cwd=Path(__file__).parent, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_paired_runner_after_completed_search(self):
        from experiments import run_experiment
        cached_main()
        rates = {name: getattr(Main, name) for name in Main.rate_names()}
        with tempfile.TemporaryDirectory() as directory:
            stats = run_experiment(make_inputs(5, 2, 4, 3), rates, 1, 1, directory)
            self.assertEqual(stats["pow"]["compute_work"]["n"], 2)
            self.assertEqual(stats["proof_paired_extra"]["total_time"]["n"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
