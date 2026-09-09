"""Calibrate node rates, run PoW/PoUW experiments, and aggregate comparable results."""

from nodes import Node
import powWorker
from tspFunctions import TspFunction
import utils
import benchmark
import multiprocessing
import secrets
from blockData import BlockData
from validation import council_validation
from validation import proof_based_validation
from fractions import Fraction
from scheduler import run_search

# Validation modes are bit flags; existing council acceptance remains unanimous.
NO_VALIDATION = 0b00
PROOF_VALIDATION = 0b01
COUNCIL_VALIDATION = 0b10


class MainFunctions:
    """Coordinate calibration, simulations, and averages for one experiment
    configuration.
    """

    benchmarks_done = False
    benchmarked_validation_mode = None
    benchmarked_num_of_cities = None
    hashes_per_second = 0.0
    computations_per_second = 0.0
    initial_validations_per_second = 0.0
    branch_validation_nodes_per_second = 0.0
    transcript_per_second = 0.0
    hash_validation_per_second = 0.0
    semantic_validation_per_second = 0.0

    def __init__(
        self,
        num_of_nodes,
        num_of_cities,
        runs,
        block_hash_difficulty,
        validation_mode,
        benchmark_progress_callback=None,
    ):
        """Store the configuration, restore or measure rates, and create the initial
        workers.
        """
        self.num_of_nodes = num_of_nodes
        self.num_of_cities = num_of_cities
        self.runs = runs
        self.block_hash_difficulty = block_hash_difficulty
        self.validation_mode = validation_mode

        # Reuse calibration only when the city count and validation mode still match.
        if (
            not MainFunctions.benchmarks_done
            or MainFunctions.benchmarked_validation_mode != self.validation_mode
            or MainFunctions.benchmarked_num_of_cities != self.num_of_cities
        ):
            self.run_benchmarks(progress_callback=benchmark_progress_callback)

        # Cached measurements still need to be converted into worker ratios each time.
        self.set_ratios()
        self.create_nodes()

    def set_ratios(self):
        """Convert cached reference throughputs into rate ratios used by every worker."""
        Node.pouw_pow_ratio = 0.0
        Node.initial_validation_pow_ratio = 0.0
        Node.branch_validation_pow_ratio = 0.0
        Node.transcript_pouw_ratio = 0.0
        Node.hash_validation_pow_ratio = 0.0
        Node.semantic_validation_pow_ratio = 0.0
        Node.pouw_pow_ratio = (
            MainFunctions.computations_per_second / MainFunctions.hashes_per_second
        )
        if self.validation_mode & COUNCIL_VALIDATION:
            Node.initial_validation_pow_ratio = (
                MainFunctions.initial_validations_per_second
                / MainFunctions.hashes_per_second
            )
            Node.branch_validation_pow_ratio = (
                MainFunctions.branch_validation_nodes_per_second
                / MainFunctions.hashes_per_second
            )
        if self.validation_mode & PROOF_VALIDATION:
            Node.transcript_pouw_ratio = (
                MainFunctions.transcript_per_second
                / MainFunctions.computations_per_second
            )
            Node.hash_validation_pow_ratio = (
                MainFunctions.hash_validation_per_second
                / MainFunctions.hashes_per_second
            )
            Node.semantic_validation_pow_ratio = (
                MainFunctions.semantic_validation_per_second
                / MainFunctions.hashes_per_second
            )

    def run_benchmarks(self, progress_callback=None):
        """Measure each required operation type and cache rates for this size and mode."""

        def benchmark_progress(step, total, message):
            """Forward calibration progress when a callback was supplied."""
            if progress_callback is not None:
                progress_callback(step, total, message)

        total_benchmarks = 2
        if self.validation_mode & COUNCIL_VALIDATION:
            total_benchmarks += 2
        if self.validation_mode & PROOF_VALIDATION:
            total_benchmarks += 3
        completed_benchmarks = 0
        benchmark_progress(
            completed_benchmarks, total_benchmarks, "Benchmarking PoW..."
        )
        MainFunctions.hashes_per_second = utils.average_runs(
            benchmark.benchmark_pow, self.runs
        )
        completed_benchmarks += 1
        benchmark_progress(
            completed_benchmarks, total_benchmarks, "Benchmarking PoUW..."
        )
        MainFunctions.computations_per_second = utils.average_runs(
            lambda: benchmark.benchmark_tsp_pouw(size=self.num_of_cities), self.runs
        )
        completed_benchmarks += 1
        if self.validation_mode & COUNCIL_VALIDATION:
            benchmark_progress(
                completed_benchmarks,
                total_benchmarks,
                "Benchmarking initial council validation...",
            )
            MainFunctions.initial_validations_per_second = utils.average_runs(
                lambda: benchmark.benchmark_initial_validation(size=self.num_of_cities),
                self.runs,
            )
            completed_benchmarks += 1
            benchmark_progress(
                completed_benchmarks,
                total_benchmarks,
                "Benchmarking council branch validation...",
            )
            MainFunctions.branch_validation_nodes_per_second = utils.average_runs(
                lambda: benchmark.benchmark_branch_validation(size=self.num_of_cities),
                self.runs,
            )
            completed_benchmarks += 1
        if self.validation_mode & PROOF_VALIDATION:
            benchmark_progress(
                completed_benchmarks,
                total_benchmarks,
                "Benchmarking transcript generation...",
            )
            MainFunctions.transcript_per_second = utils.average_runs(
                lambda: benchmark.benchmark_transcript(size=self.num_of_cities),
                self.runs,
            )
            completed_benchmarks += 1
            benchmark_progress(
                completed_benchmarks,
                total_benchmarks,
                "Benchmarking transcript hash validation...",
            )
            MainFunctions.hash_validation_per_second = utils.average_runs(
                lambda: benchmark.benchmark_hash_validation(size=self.num_of_cities),
                self.runs,
            )
            completed_benchmarks += 1
            benchmark_progress(
                completed_benchmarks,
                total_benchmarks,
                "Benchmarking Proof semantic validation...",
            )
            MainFunctions.semantic_validation_per_second = utils.average_runs(
                lambda: benchmark.benchmark_semantic_validation(
                    size=self.num_of_cities
                ),
                self.runs,
            )
            completed_benchmarks += 1
        benchmark_progress(
            completed_benchmarks, total_benchmarks, "Benchmarks complete."
        )
        MainFunctions.benchmarks_done = True
        MainFunctions.benchmarked_validation_mode = self.validation_mode
        MainFunctions.benchmarked_num_of_cities = self.num_of_cities

    def create_nodes(self):
        """Generate a new shared TSP, reset the transcript, and create worker
        capabilities.
        """
        Node.initialize_tsp(self.num_of_cities)

        # Discard the previous run's transcript, including when switching validation mode.
        Node.transcript = None
        if self.validation_mode & PROOF_VALIDATION:

            # Setup commits the root and matrix; it is outside the modeled mining phase.
            self.transcript_sigma = secrets.token_bytes(32)
            root = Node.tsp.tsp_root
            root_children = []
            for neighbour in range(root.size):
                if root.matrix[root.vertex][neighbour] == utils.inf:
                    continue
                if neighbour in root.path:
                    continue
                child = TspFunction._create_child(
                    root, Node.tsp.matrix, root.vertex, neighbour
                )
                edge_cost = Node.tsp.matrix[root.vertex][neighbour]
                reduced_edge_cost = root.matrix[root.vertex][neighbour]
                reduction_cost = child.cost - root.cost - reduced_edge_cost
                root_children.append(
                    {
                        "selected_neighbour": neighbour,
                        "child_path": child.path[:],
                        "edge_cost": edge_cost,
                        "reduction_cost": reduction_cost,
                        "child_lower_bound": child.cost,
                    }
                )
            root_data = {
                "path": root.path[:],
                "vertex": root.vertex,
                "visited": root.visited,
                "lower_bound": root.cost,
                "children": root_children,
            }
            self.transcript_root = utils.create_hash(
                self.transcript_sigma.hex() + str(root_data) + str(Node.tsp.matrix)
            )
            Node.initialize_transcript(root_data, self.transcript_root)
        self.node_list = []
        for i in range(self.num_of_nodes):
            node = Node(f"node{i + 1}")
            self.node_list.append(node)
        if all((node.search_rate <= 0 for node in self.node_list)):
            raise RuntimeError("All PoUW search rates are zero")

    def multiple_node_pow(self, block_hash_difficulty):
        """Mine until the earliest simulated success and return exact cutoff counts and
        time.
        """
        with multiprocessing.Pool(processes=len(self.node_list)) as pool:
            while not Node.found:
                arguments = [
                    (
                        node.nonce,
                        node.coinbase["extra_nonce"],
                        node.coinbase["reward"],
                        node.merkle_root,
                        node.hash_rate,
                        node.blockData.previous_hash,
                        node.blockData.timestamp,
                        block_hash_difficulty,
                        node.blockData.transactions,
                    )
                    for node in self.node_list
                ]
                results = pool.map(powWorker.pow_worker, arguments)
                successful_nodes = [
                    (index, result)
                    for index, result in enumerate(results)
                    if result["found"]
                ]
                if not successful_nodes:
                    for node, result in zip(self.node_list, results):
                        node.update_pow_state(result)
                    Node.simulation_time += 1
                    continue

                # Compare exact fractions; worker index deterministically resolves equal success times.
                winner_index, winner = min(
                    successful_nodes,
                    key=lambda item: (
                        Fraction(item[1]["hashes"], self.node_list[item[0]].hash_rate),
                        item[0],
                    ),
                )
                finishing_node = self.node_list[winner_index]
                hashes = winner["hashes"]
                cutoff = Fraction(hashes, finishing_node.hash_rate)
                winner_time = float(cutoff)
                for node in self.node_list:

                    # Count completed hashes only; never round a partial attempt up.
                    work_done = node.hash_rate * cutoff.numerator // cutoff.denominator
                    node.mining_count += work_done
                    powWorker.advance_state(node, work_done)
                finishing_node.header_hash = winner["header_hash"]
                Node.simulation_time += winner_time
                Node.found = True
                total_mining_count = sum((node.mining_count for node in self.node_list))
                pow_work = total_mining_count / MainFunctions.hashes_per_second
                return {
                    "total_hashes": total_mining_count,
                    "compute_work": pow_work,
                    "simulation_time": Node.simulation_time,
                    "winner": {
                        "name": finishing_node.name,
                        "hashes": winner["hashes"],
                        "nonce": winner["nonce"],
                        "extra_nonce": winner["extra_nonce"],
                        "header_hash": winner["header_hash"],
                    },
                    "nodes": {
                        node.name: {
                            "hash_rate": node.hash_rate,
                            "hashes": node.mining_count,
                        }
                        for node in self.node_list
                    },
                }

    def multiple_node_pouw_tsp(self):
        """Run causal search, validate if requested, and report raw counts and
        normalized work.
        """
        if all((node.search_rate <= 0 for node in self.node_list)):
            raise RuntimeError("All PoUW search rates are zero")
        pouw_time = 0.0
        validation_time = 0.0
        validation_valid = True
        validation_compute_work = 0.0
        council_initial_validations = 0
        council_branch_validation_nodes = 0
        council_initial_compute_work = 0.0
        council_branch_compute_work = 0.0
        council_compute_work = 0.0

        # The scheduler waits for reserved tasks and pending transcript appends.
        search_result = run_search(
            Node.tsp, self.node_list, Node.transcript, Node.transcript_pouw_ratio
        )
        pouw_time = search_result["time"]
        finishing_node = search_result["finishing_node"]
        discovering_node = search_result["discovering_node"]
        transcript_records = search_result["transcript_records"]
        Node.found = True
        Node.simulation_time = pouw_time
        winning_node = self.node_list[0].tsp.best_node
        pouw_computations = sum((node.computations for node in self.node_list))

        # Normalize each operation type separately into reference-machine seconds.
        search_compute_work = pouw_computations / MainFunctions.computations_per_second
        transcript_compute_work = (
            transcript_records / MainFunctions.transcript_per_second
            if transcript_records
            else 0.0
        )

        # Include transcript generation once, separately from verification.
        pouw_compute_work = search_compute_work + transcript_compute_work
        proof_hash_checks = proof_semantic_checks = 0
        proof_hash_compute_work = proof_semantic_compute_work = 0.0
        if self.validation_mode & PROOF_VALIDATION:
            validators = [node for node in self.node_list if node is not finishing_node]
            proof_result = proof_based_validation(
                self.node_list[0].tsp,
                self.node_list[0].tsp.best_path,
                self.node_list[0].tsp.best_cost,
                Node.transcript,
                validators,
                self.transcript_sigma,
                self.transcript_root,
            )
            validation_valid = validation_valid and proof_result["valid"]
            validation_time += proof_result["validation_time"]
            proof_hash_checks = proof_result["hash_checks"]
            proof_semantic_checks = proof_result["semantic_checks"]
            proof_hash_compute_work = (
                proof_result["hash_checks"] / MainFunctions.hash_validation_per_second
            )
            proof_semantic_compute_work = (
                proof_result["semantic_checks"]
                / MainFunctions.semantic_validation_per_second
            )
            proof_compute_work = proof_hash_compute_work + proof_semantic_compute_work
            validation_compute_work += proof_compute_work
        if self.validation_mode & COUNCIL_VALIDATION:
            council = [node for node in self.node_list if node is not finishing_node]
            council_result = council_validation(
                self.node_list[0].tsp,
                council,
                self.node_list[0].tsp.best_path,
                self.node_list[0].tsp.best_cost,
                MainFunctions.initial_validations_per_second,
                MainFunctions.branch_validation_nodes_per_second,
            )
            validation_valid = validation_valid and council_result["valid"]
            validation_time += council_result["validation_time"]
            council_initial_validations = council_result["initial_validations"]
            council_branch_validation_nodes = council_result["branch_validation_nodes"]
            council_initial_compute_work = council_result["initial_compute_work"]
            council_branch_compute_work = council_result["branch_compute_work"]
            council_compute_work = council_result["compute_work"]
            validation_compute_work += council_compute_work

        # Compatibility field: this is B&B-equivalent work, not a raw operation count.
        validation_computations = (
            validation_compute_work * MainFunctions.computations_per_second
        )
        total_computations = (
            pouw_compute_work * MainFunctions.computations_per_second
            + validation_computations
        )
        total_compute_work = pouw_compute_work + validation_compute_work

        # Validation follows search; elapsed time and aggregate work are separate metrics.
        total_time = pouw_time + validation_time
        Node.simulation_time = total_time
        return {
            "pouw_computations": pouw_computations,
            "search_compute_work": search_compute_work,
            "transcript_records": transcript_records,
            "transcript_compute_work": transcript_compute_work,
            "proof_hash_checks": proof_hash_checks,
            "proof_semantic_checks": proof_semantic_checks,
            "proof_hash_compute_work": proof_hash_compute_work,
            "proof_semantic_compute_work": proof_semantic_compute_work,
            "finishing_node": finishing_node.name,
            "discovering_node": discovering_node.name,
            "pouw_compute_work": pouw_compute_work,
            "pouw_time": pouw_time,
            "validation_computations": validation_computations,
            "validation_compute_work": validation_compute_work,
            "validation_time": validation_time,
            "validation_valid": validation_valid,
            "total_computations": total_computations,
            "total_compute_work": total_compute_work,
            "total_time": total_time,
            "simulation_time": total_time,
            "council_initial_validations": council_initial_validations,
            "council_branch_validation_nodes": council_branch_validation_nodes,
            "council_initial_compute_work": council_initial_compute_work,
            "council_branch_compute_work": council_branch_compute_work,
            "council_compute_work": council_compute_work,
            "winner": {
                "name": discovering_node.name,
                # Use the closed tour, not the partial search node before its return edge.
                "path": Node.tsp.best_path[:],
                "cost": Node.tsp.best_cost,
                "total_cost": Node.tsp.best_cost,
                "vertex": Node.tsp.best_path[-1],
                "visited": Node.tsp.size,
                "lower_bound": winning_node.cost,
                "partial_path_cost": winning_node.total_cost,
            },
            "nodes": {
                node.name: {
                    "hash_rate": node.hash_rate,
                    "search_rate": node.search_rate,
                    "computations": node.computations,
                }
                for node in self.node_list
            },
        }

    def run_simulation(self, progress_callback=None):
        """Repeat both algorithms and average successful results; reject failed
        validation.
        """
        total_runs = self.runs * 2
        completed_runs = 0

        def update_progress():
            """Advance the completed-run counter and notify the optional progress
            callback.
            """
            nonlocal completed_runs
            completed_runs += 1
            if progress_callback is not None:
                progress_callback(completed_runs, total_runs)

        # Run each repetition with fresh per-run state before calculating averages.
        pow_results = []
        for i in range(self.runs):
            self.reset_simulation()
            result = self.multiple_node_pow(self.block_hash_difficulty)
            pow_results.append(result)
            update_progress()
        pouw_results = []
        for i in range(self.runs):
            self.reset_simulation()
            result = self.multiple_node_pouw_tsp()
            if self.validation_mode != NO_VALIDATION and (
                not result["validation_valid"]
            ):
                raise RuntimeError("PoUW solution failed validation and was rejected.")
            pouw_results.append(result)
            update_progress()
        average_hashes = sum((result["total_hashes"] for result in pow_results)) / len(
            pow_results
        )
        average_computations = sum(
            (result["pouw_computations"] for result in pouw_results)
        ) / len(pouw_results)
        average_pow_compute_work = sum(
            (result["compute_work"] for result in pow_results)
        ) / len(pow_results)
        average_pouw_compute_work = sum(
            (result["pouw_compute_work"] for result in pouw_results)
        ) / len(pouw_results)
        average_validation_compute_work = sum(
            (result["validation_compute_work"] for result in pouw_results)
        ) / len(pouw_results)
        average_validated_pouw_compute_work = sum(
            (result["total_compute_work"] for result in pouw_results)
        ) / len(pouw_results)
        average_pow_simulation_time = sum(
            (result["simulation_time"] for result in pow_results)
        ) / len(pow_results)
        average_pouw_simulation_time = sum(
            (result["pouw_time"] for result in pouw_results)
        ) / len(pouw_results)
        average_validation_time = sum(
            (result["validation_time"] for result in pouw_results)
        ) / len(pouw_results)
        average_validated_pouw_simulation_time = sum(
            (result["total_time"] for result in pouw_results)
        ) / len(pouw_results)
        average_pow_hash_rate = {}
        for node_name in pow_results[0]["nodes"]:
            average_pow_hash_rate[node_name] = sum(
                (run["nodes"][node_name]["hash_rate"] for run in pow_results)
            ) / len(pow_results)
        average_pouw_hash_rate = {}
        for node_name in pouw_results[0]["nodes"]:
            average_pouw_hash_rate[node_name] = sum(
                (run["nodes"][node_name]["hash_rate"] for run in pouw_results)
            ) / len(pouw_results)
        average_pouw_search_rate = {}
        for node_name in pouw_results[0]["nodes"]:
            average_pouw_search_rate[node_name] = sum(
                (run["nodes"][node_name]["search_rate"] for run in pouw_results)
            ) / len(pouw_results)
        average_pow_mining_count = {}
        for node_name in pow_results[0]["nodes"]:
            average_pow_mining_count[node_name] = sum(
                (run["nodes"][node_name]["hashes"] for run in pow_results)
            ) / len(pow_results)
        average_pouw_computations = {}
        for node_name in pouw_results[0]["nodes"]:
            average_pouw_computations[node_name] = sum(
                (run["nodes"][node_name]["computations"] for run in pouw_results)
            ) / len(pouw_results)
        return {
            "average_hashes": average_hashes,
            "average_computations": average_computations,
            "average_pow_compute_work": average_pow_compute_work,
            "average_pouw_compute_work": average_pouw_compute_work,
            "average_validation_compute_work": average_validation_compute_work,
            "average_validated_pouw_compute_work": average_validated_pouw_compute_work,
            "average_pow_simulation_time": average_pow_simulation_time,
            "average_pouw_simulation_time": average_pouw_simulation_time,
            "average_validation_time": average_validation_time,
            "average_validated_pouw_simulation_time": average_validated_pouw_simulation_time,
            "pow": {
                "average_hash_rate": average_pow_hash_rate,
                "average_mining_count": average_pow_mining_count,
                "runs": pow_results,
            },
            "pouw": {
                "average_hash_rate": average_pouw_hash_rate,
                "average_search_rate": average_pouw_search_rate,
                "average_computations": average_pouw_computations,
                "average_compute_work": average_pouw_compute_work,
                "average_simulation_time": average_pouw_simulation_time,
                "runs": pouw_results,
            },
            "validated_pouw": {
                "average_compute_work": average_validated_pouw_compute_work,
                "average_validation_compute_work": average_validation_compute_work,
                "average_simulation_time": average_validated_pouw_simulation_time,
                "average_validation_time": average_validation_time,
                "runs": pouw_results,
            },
        }

    def reset_simulation(self):
        """Reset per-run counters and create a fresh TSP and worker list without
        recalibration.
        """
        Node.blockData = BlockData()
        Node.found = False
        Node.simulation_time = 0.0
        Node.transcript = None
        self.create_nodes()
