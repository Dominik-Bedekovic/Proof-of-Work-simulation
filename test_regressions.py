"""Regression tests for solver correctness, validation, scheduling, and accounting."""

import contextlib, copy, io, itertools, multiprocessing, random, sys, unittest
from types import SimpleNamespace
from unittest.mock import patch
import benchmark, proof_validation_tests as proofs, powWorker, utils, validation
from mainFunctions import MainFunctions as Main
from nodes import Node
from scheduler import run_search
from tspData import TspData
from tspFunctions import TspFunction as F

MATRIX = [
    [utils.inf, 250, 700, 40, 840],
    [250, utils.inf, 120, 790, 640],
    [700, 120, utils.inf, 60, 40],
    [40, 790, 60, utils.inf, 600],
    [840, 640, 40, 600, utils.inf],
]


def make_tsp(a):
    """Create a fresh search instance from the test's explicit distance matrix."""
    with patch.object(F, "_make_tsp_matrix", return_value=copy.deepcopy(a)):
        return TspData(len(a))


def proof_for(a):
    """Generate a genuine certificate for an explicit test matrix."""
    with patch.object(proofs, "TspData", side_effect=lambda n, b: make_tsp(a)):
        return proofs.create_genuine_proof(len(a))


def oracle(a):
    """Enumerate every tour from city zero to obtain an independent optimal-cost
    reference.
    """
    return min(
        (
            sum((a[x][y] for x, y in zip(p, p[1:])))
            for rest in itertools.permutations(range(1, len(a)))
            for p in [[0, *rest, 0]]
        )
    )


def cached_main(mode=0, size=5, workers=4, runs=1):
    """Provide fixed calibration rates for reproducible integration and accounting
    assertions.
    """
    for k, v in {
        "hashes_per_second": 1000.0,
        "computations_per_second": 100.0,
        "initial_validations_per_second": 1000.0,
        "branch_validation_nodes_per_second": 100.0,
        "transcript_per_second": 200.0,
        "hash_validation_per_second": 500.0,
        "semantic_validation_per_second": 100.0,
    }.items():
        setattr(Main, k, v)
    Main.benchmarks_done = True
    Main.benchmarked_validation_mode = mode
    Main.benchmarked_num_of_cities = size
    return Main(workers, size, runs, 1, mode)


class Regressions(unittest.TestCase):
    """Check the reviewed correctness failures and their expected corrected behavior."""

    def setUp(self):
        """Reset shared state and capture diagnostic output for each independent test."""
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        Node.transcript = None
        Node.found = False
        Node.simulation_time = 0

    def tearDown(self):
        """Restore normal console output after each test."""
        self.output.__exit__(None, None, None)

    def test_original_five_city_false_pair(self):
        """Reject the 1870-cost route when it claims the genuine optimum cost of 1030."""
        t, p, c, tr, vs, sigma, root = proof_for(MATRIX)
        fake = [0, 1, 2, 3, 4, 0]
        self.assertEqual(c, 1030)
        self.assertEqual(sum((MATRIX[x][y] for x, y in zip(fake, fake[1:]))), 1870)
        self.assertFalse(proofs.validate(t, fake, c, tr, vs, sigma, root))
        self.assertFalse(
            validation._validate_transcript_semantics(t, tr, fake, c, False)[0]
        )

    def test_seven_city_false_pair(self):
        """Reject the second reviewed false route/cost pair on the deterministic seven-
        city instance.
        """
        t, p, c, tr, vs, sigma, root = proofs.create_genuine_proof()
        fake = p[:]
        fake[1], fake[2] = (fake[2], fake[1])
        self.assertEqual(c, 1813)
        self.assertEqual(sum((t.matrix[x][y] for x, y in zip(fake, fake[1:]))), 2587)
        self.assertFalse(proofs.validate(t, fake, c, tr, vs, sigma, root))

    def test_equal_optimum_alternative_allowed(self):
        """Accept the reversed orientation of a symmetric optimal tour."""
        t, p, c, tr, vs, sigma, root = proof_for(MATRIX)
        reverse = list(reversed(p))
        self.assertNotEqual(p, reverse)
        self.assertTrue(proofs.validate(t, reverse, c, tr, vs, sigma, root))

    def test_malformed_vertices_costs_and_missing_edges(self):
        """Reject malformed city indices, invalid costs, and a missing tour edge."""
        t, p, c, tr, vs, sigma, root = proof_for(MATRIX)
        paths = [None, "012340", [0, 1, 0], [0, 1, 1, 3, 4, 0], [1, 0, 2, 3, 4, 1]]
        for v in (True, 1.0, "1", None, -1, 5, [], float("nan")):
            q = p[:]
            q[1] = v
            paths.append(q)
        for q in paths:
            with self.subTest(path=q):
                self.assertFalse(proofs.validate(t, q, c, tr, vs, sigma, root))
        for cost in (True, "1030", None, float("nan"), float("inf"), -1, c + 1):
            with self.subTest(cost=cost):
                self.assertFalse(proofs.validate(t, p, cost, tr, vs, sigma, root))
        t.matrix[p[0]][p[1]] = utils.inf
        self.assertFalse(proofs.validate(t, p, c, tr, vs, sigma, root))

    def test_original_adversarial_suite(self):
        """Require every original honest/adversarial test to return its expected
        decision.
        """
        for name in sorted((n for n in dir(proofs) if n.startswith("test_"))):
            with self.subTest(name=name):
                self.assertEqual(getattr(proofs, name)(), name == "test_honest_proof")

    def test_solver_against_600_exhaustive_instances(self):
        """Compare optimal costs against enumeration on 600 complete symmetric small
        instances.
        """
        rng = random.Random(20260909)
        for n in range(3, 9):
            for j in range(100):
                a = [[utils.inf] * n for _ in range(n)]
                for x in range(n):
                    for y in range(x + 1, n):
                        a[x][y] = a[y][x] = rng.randint(1, 10 if j < 30 else 1000)
                t = make_tsp(a)
                F.tsp_solver(t)
                with self.subTest(size=n, instance=j):
                    self.assertEqual(t.best_cost, oracle(a))

    def test_council_rejects_original_1050(self):
        """Ensure a branch finding a better tour rejects the old nonoptimal proposal."""
        self.assertEqual(
            [F.validate_branch(make_tsp(MATRIX), [0, c], 1050)[0] for c in range(1, 5)],
            [False, True, False, True],
        )

    def test_actual_parent_availability(self):
        """Ensure every child begins after its parent completes and each task consumes
        its full duration.
        """
        m = cached_main(size=3, workers=3)
        for n in m.node_list:
            n.search_rate = 1
        trace = []
        run_search(
            Node.tsp,
            m.node_list,
            on_event=lambda k, t, n, p: trace.append((k, t, tuple(p.path))),
        )
        starts = {p: t for k, t, p in trace if k == "dispatch"}
        ends = {p: t for k, t, p in trace if k == "search_complete"}
        self.assertEqual(ends[0,], 1)
        for p, t in starts.items():
            self.assertEqual(ends[p] - t, 1)
            if len(p) > 1:
                self.assertGreaterEqual(t, ends[p[:-1]])

    def test_dependency_chain_three_seconds(self):
        """Verify three dependent one-second tasks still take three seconds with
        multiple workers.
        """
        m = cached_main(workers=3)
        for n in m.node_list:
            n.search_rate = 1

        def step(local, *args):
            """Supply a controlled one-task result for the scheduler test's hand-
            calculable workload.
            """
            task = local.priority_queue.pop()
            depth = len(task.path)
            if depth < 3:
                child = copy.copy(task)
                child.path = task.path + [depth]
                local.priority_queue.append(child)
            else:
                local.best_cost = 1
                local.best_path = [0, 1, 2, 0]
                local.best_node = task
            return (1, 1.0, 0.0, not local.priority_queue)

        with patch.object(F, "tsp_solver", side_effect=step):
            result = run_search(Node.tsp, m.node_list)
        self.assertEqual(result["time"], 3)
        self.assertEqual(sum((n.computations for n in m.node_list)), 3)

    def test_final_transcript_drained(self):
        """Ensure the final record appends finish before the search phase ends."""
        m = cached_main(workers=1)
        m.node_list[0].search_rate = 1
        tr = SimpleNamespace(steps=[])

        def step(local, *args):
            """Supply a controlled one-task result for the scheduler test's hand-
            calculable workload.
            """
            task = local.priority_queue.pop()
            local.best_cost = 1
            local.best_path = [0, 1, 0]
            local.best_node = task
            tr.steps.extend([{}, {}])
            return (1, 3.0, 2.0, True)

        with patch.object(F, "tsp_solver", side_effect=step):
            result = run_search(Node.tsp, m.node_list, tr, 1)
        self.assertEqual(result["time"], 3)
        self.assertEqual(result["transcript_records"], 2)
        self.assertEqual(m.node_list[0].work, 3)

    def test_all_inflight_tasks_and_slow_logging_drained(self):
        """Wait for every reserved task and ordered append batch, including the slowest
        worker.
        """
        m = cached_main(workers=2)
        for n in m.node_list:
            n.search_rate = 1
        tr = SimpleNamespace(steps=[])

        def step(local, *args):
            """Supply a controlled one-task result for the scheduler test's hand-
            calculable workload.
            """
            task = local.priority_queue.pop()
            if task.path == [0]:
                for v in (1, 2):
                    child = copy.copy(task)
                    child.path = [0, v]
                    local.priority_queue.append(child)
                logs = 0
            else:
                if task.path == [0, 1]:
                    local.best_cost = 1
                    local.best_path = [0, 1, 0]
                    local.best_node = task
                    logs = 5
                else:
                    logs = 1
                tr.steps.extend([{}] * logs)
            return (1, 1.0 + logs, float(logs), not local.priority_queue)

        with patch.object(F, "tsp_solver", side_effect=step):
            result = run_search(Node.tsp, m.node_list, tr, 1)
        self.assertEqual(result["time"], 8)
        self.assertEqual(result["transcript_records"], 6)
        self.assertEqual(sum((n.computations for n in m.node_list)), 3)

    def test_parallel_transcripts_and_optima(self):
        """Check heterogeneous-worker schedules against enumeration and semantic
        replay.
        """
        rng = random.Random(7129)
        nonminimum = False
        for trial in range(30):
            size = 5 + trial % 3
            a = [[utils.inf] * size for _ in range(size)]
            for x in range(size):
                for y in range(x + 1, size):
                    a[x][y] = a[y][x] = rng.randint(1, 100)
            with patch.object(F, "_make_tsp_matrix", return_value=a):
                m = cached_main(1, size, 4)
            for n, r in zip(m.node_list, [1, 3, 7, 11]):
                n.search_rate = r
            trace = []

            def event(k, t, n, p):
                """Collect actual completion paths and bounds for comparison with the
                replay frontier.
                """
                if k == "search_complete":
                    trace.append((tuple(p.path), p.cost))

            result = run_search(
                Node.tsp,
                m.node_list,
                Node.transcript,
                Node.transcript_pouw_ratio,
                event,
            )
            self.assertEqual(Node.tsp.best_cost, oracle(a))
            self.assertEqual(result["transcript_records"], len(Node.transcript.steps))
            self.assertTrue(
                proofs.validate(
                    Node.tsp,
                    Node.tsp.best_path,
                    Node.tsp.best_cost,
                    Node.transcript,
                    m.node_list,
                    m.transcript_sigma,
                    m.transcript_root,
                )
            )
            frontier = {(0,): Node.tsp.tsp_root.cost}
            for path, bound in trace:
                if bound > min(frontier.values()):
                    nonminimum = True
                del frontier[path]
                for record in Node.transcript.steps:
                    d = record["data"]
                    if (
                        d["type"] == "branch"
                        and tuple(d["parent_path"]) == path
                        and (not d["pruned"])
                    ):
                        frontier[tuple(d["child_path"])] = d["child_lower_bound"]
        self.assertTrue(nonminimum, "Must exercise nonserial completion order.")

    def test_repeat_modes_accounting_and_payload(self):
        """Check repeated runs, state resets, returned tours, and component work sums
        in all modes.
        """
        for mode in (0, 1, 2):
            for repeat in range(2):
                m = cached_main(mode, runs=2)
                data = m.run_simulation()
                self.assertEqual(len(data["pouw"]["runs"]), 2)
                for r in data["pouw"]["runs"]:
                    self.assertTrue(r["validation_valid"])
                    self.assertEqual(len(r["winner"]["path"]), 6)
                    self.assertEqual(r["winner"]["path"][0], r["winner"]["path"][-1])
                    self.assertEqual(r["winner"]["cost"], r["winner"]["total_cost"])
                    parts = sum(
                        (
                            r[k]
                            for k in [
                                "search_compute_work",
                                "transcript_compute_work",
                                "proof_hash_compute_work",
                                "proof_semantic_compute_work",
                                "council_initial_compute_work",
                                "council_branch_compute_work",
                            ]
                        )
                    )
                    self.assertAlmostEqual(r["total_compute_work"], parts)
                    self.assertAlmostEqual(
                        r["transcript_compute_work"], r["transcript_records"] / 200.0
                    )
                last = data["pouw"]["runs"][-1]
                self.assertEqual(last["winner"]["path"], Node.tsp.best_path)
                self.assertEqual(last["winner"]["cost"], Node.tsp.best_cost)
                self.assertAlmostEqual(
                    sum((n.work for n in m.node_list)) / 100.0,
                    last["pouw_compute_work"],
                )
                if mode != 1:
                    self.assertIsNone(Node.transcript)

    def test_original_solution_payload(self):
        """Require a closed 1030-cost tour in either orientation and correct discoverer
        attribution.
        """
        with patch.object(F, "_make_tsp_matrix", return_value=MATRIX):
            m = cached_main()
        r = m.multiple_node_pouw_tsp()
        self.assertEqual(r["winner"]["total_cost"], 1030)
        path = r["winner"]["path"]
        self.assertIn(path, [[0, 1, 4, 2, 3, 0], [0, 3, 2, 4, 1, 0]])
        self.assertEqual(r["winner"]["name"], r["discovering_node"])

    def test_pow_earliest_winner_counts_cursor_and_ties(self):
        """Check earliest success, floor counts, deterministic ties, and next-attempt
        cursors.
        """
        for rates, hashes, elapsed, counts, winner in [
            ([100, 100], [90, 10], 0.1, [10, 10], "node2"),
            ([10, 6], [1, None], 0.1, [1, 0], "node1"),
            ([10, 20], [1, 2], 0.1, [1, 2], "node1"),
        ]:
            m = cached_main(workers=2)
            Node.found = False
            Node.simulation_time = 0
            for n, r in zip(m.node_list, rates):
                n.hash_rate = r

            class Pool:
                """In-process pool substitute returning deterministic PoW successes for
                cutoff tests.
                """

                def __init__(self, *a, **k):
                    """Accept the pool constructor arguments used by the simulation."""
                    pass

                def __enter__(self):
                    """Return the fake pool for the with statement."""
                    return self

                def __exit__(self, *a):
                    """Finish the fake pool context without suppressing exceptions."""
                    pass

                def map(self, *a):
                    """Return the prescribed worker results instead of executing real
                    hash searches.
                    """
                    return [
                        dict(
                            found=h is not None,
                            hashes=h or r,
                            nonce=(h or r) - 1,
                            extra_nonce=0,
                            merkle_root="test",
                            header_hash="0test",
                        )
                        for r, h in zip(rates, hashes)
                    ]

            with patch("mainFunctions.multiprocessing.Pool", Pool):
                r = m.multiple_node_pow(1)
            self.assertEqual(r["winner"]["name"], winner)
            self.assertEqual(r["simulation_time"], elapsed)
            self.assertEqual([n.mining_count for n in m.node_list], counts)
            self.assertEqual([n.nonce for n in m.node_list], counts)

    def test_pow_nonce_wrap(self):
        """Advance the extra nonce and transaction digest when the ordinary nonce
        wraps.
        """
        m = cached_main(workers=1)
        n = m.node_list[0]
        n.nonce = 2**32 - 1
        old = n.merkle_root
        powWorker.advance_state(n, 2)
        self.assertEqual(n.nonce, 1)
        self.assertEqual(n.coinbase["extra_nonce"], 1)
        self.assertNotEqual(n.merkle_root, old)

    def test_invalid_run_rejected(self):
        """Ensure a failed validation is rejected before successful-run statistics are
        formed.
        """
        m = cached_main(1)
        with patch.object(m, "multiple_node_pow", return_value={}), patch.object(
            m, "multiple_node_pouw_tsp", return_value={"validation_valid": False}
        ):
            with self.assertRaises(RuntimeError):
                m.run_simulation()

    def test_benchmark_components(self):
        """Ensure all component calibrators execute verified positive-throughput
        workloads.
        """
        for name in (
            "benchmark_tsp_pouw",
            "benchmark_initial_validation",
            "benchmark_branch_validation",
            "benchmark_transcript",
            "benchmark_hash_validation",
            "benchmark_semantic_validation",
        ):
            with self.subTest(name=name):
                self.assertGreater(getattr(benchmark, name)(duration=0.03, size=5), 0)


if __name__ == "__main__":
    if "--spawn" in sys.argv:
        sys.argv.remove("--spawn")
        multiprocessing.set_start_method("spawn")
    unittest.main(verbosity=2)
