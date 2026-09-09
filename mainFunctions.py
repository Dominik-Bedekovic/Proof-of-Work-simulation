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
import heapq
from fractions import Fraction
from scheduler import run_search

# Validation modes
NO_VALIDATION = 0b00
PROOF_VALIDATION = 0b01
COUNCIL_VALIDATION = 0b10

class MainFunctions:

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
        benchmark_progress_callback=None
    ):

        # Store the simulation parameters.
        self.num_of_nodes = num_of_nodes
        self.num_of_cities = num_of_cities
        self.runs = runs
        self.block_hash_difficulty = block_hash_difficulty
        self.validation_mode = validation_mode

        # -----------------------------------------------------
        # BENCHMARK CALIBRATION
        # -----------------------------------------------------
        # Run the benchmarks if they have not yet been measured
        # or if the selected validation mode requires a different
        # benchmark configuration.
        if (
            not MainFunctions.benchmarks_done
            or
            MainFunctions.benchmarked_validation_mode
            != self.validation_mode
            or
            MainFunctions.benchmarked_num_of_cities
            != self.num_of_cities
        ):

            self.run_benchmarks(
                progress_callback=benchmark_progress_callback
            )

        # Restore all node-rate ratios from the cached
        # benchmark measurements.
        self.set_ratios()

        # Create the nodes only after all rate ratios
        # have been initialized.
        self.create_nodes()

    def set_ratios(self):

        # -----------------------------------------------------
        # RESET RATIOS
        # -----------------------------------------------------

        Node.pouw_pow_ratio = 0.0

        Node.initial_validation_pow_ratio = 0.0
        Node.branch_validation_pow_ratio = 0.0

        Node.transcript_pouw_ratio = 0.0
        Node.hash_validation_pow_ratio = 0.0
        Node.semantic_validation_pow_ratio = 0.0

        # -----------------------------------------------------
        # BASE POUW / POW RATIO
        # -----------------------------------------------------

        Node.pouw_pow_ratio = (
            MainFunctions.computations_per_second
            / MainFunctions.hashes_per_second
        )

        # -----------------------------------------------------
        # COUNCIL VALIDATION
        # -----------------------------------------------------

        if self.validation_mode & COUNCIL_VALIDATION:

            Node.initial_validation_pow_ratio = (
                MainFunctions.initial_validations_per_second
                / MainFunctions.hashes_per_second
            )

            Node.branch_validation_pow_ratio = (
                MainFunctions.branch_validation_nodes_per_second
                / MainFunctions.hashes_per_second
            )

        # -----------------------------------------------------
        # PROOF VALIDATION
        # -----------------------------------------------------

        if self.validation_mode & PROOF_VALIDATION:

            # Transcript-generation throughput is compared against
            # the PoUW B&B throughput because tsp_solver converts
            # transcript overhead into B&B-equivalent work.
            Node.transcript_pouw_ratio = (
                MainFunctions.transcript_per_second
                / MainFunctions.computations_per_second
            )

            # Hash validation is derived from each node's hash rate.
            Node.hash_validation_pow_ratio = (
                MainFunctions.hash_validation_per_second
                / MainFunctions.hashes_per_second
            )

            # Complete semantic replay is also derived from
            # each simulated node's computational capability.
            Node.semantic_validation_pow_ratio = (
                MainFunctions.semantic_validation_per_second
                / MainFunctions.hashes_per_second
            )

    def run_benchmarks(self, progress_callback=None):

        def benchmark_progress(step, total, message):

            if progress_callback is not None:

                progress_callback(
                    step,
                    total,
                    message
                )

        # =========================================================
        # NUMBER OF BENCHMARKS
        # =========================================================

        # Base:
        # 1. PoW
        # 2. PoUW
        total_benchmarks = 2

        # Council:
        # 3. Initial validation
        # 4. Branch validation
        if self.validation_mode & COUNCIL_VALIDATION:
            total_benchmarks += 2

        # Proof:
        # 3/5. Transcript generation
        # 4/6. Hash-chain validation
        # 5/7. Complete semantic B&B replay
        if self.validation_mode & PROOF_VALIDATION:
            total_benchmarks += 3

        completed_benchmarks = 0

        # =========================================================
        # POW
        # =========================================================

        benchmark_progress(
            completed_benchmarks,
            total_benchmarks,
            "Benchmarking PoW..."
        )

        MainFunctions.hashes_per_second = (
            utils.average_runs(
                benchmark.benchmark_pow,
                self.runs
            )
        )

        completed_benchmarks += 1

        # =========================================================
        # POUW
        # =========================================================

        benchmark_progress(
            completed_benchmarks,
            total_benchmarks,
            "Benchmarking PoUW..."
        )

        MainFunctions.computations_per_second = (
            utils.average_runs(
                lambda:
                    benchmark.benchmark_tsp_pouw(
                        size=self.num_of_cities
                    ),
                self.runs
            )
        )

        completed_benchmarks += 1

        # =========================================================
        # COUNCIL VALIDATION
        # =========================================================

        if self.validation_mode & COUNCIL_VALIDATION:

            # -----------------------------------------------------
            # Initial complete-tour validation
            # -----------------------------------------------------

            benchmark_progress(
                completed_benchmarks,
                total_benchmarks,
                "Benchmarking initial council validation..."
            )

            MainFunctions.initial_validations_per_second = (
                utils.average_runs(
                    lambda:
                        benchmark.benchmark_initial_validation(
                            size=self.num_of_cities
                        ),
                    self.runs
                )
            )

            completed_benchmarks += 1

            # -----------------------------------------------------
            # Branch validation
            # -----------------------------------------------------

            benchmark_progress(
                completed_benchmarks,
                total_benchmarks,
                "Benchmarking council branch validation..."
            )

            MainFunctions.branch_validation_nodes_per_second = (
                utils.average_runs(
                    lambda:
                        benchmark.benchmark_branch_validation(
                            size=self.num_of_cities
                        ),
                    self.runs
                )
            )

            completed_benchmarks += 1

        # =========================================================
        # PROOF VALIDATION
        # =========================================================

        if self.validation_mode & PROOF_VALIDATION:

            # -----------------------------------------------------
            # Transcript generation
            # -----------------------------------------------------

            benchmark_progress(
                completed_benchmarks,
                total_benchmarks,
                "Benchmarking transcript generation..."
            )

            MainFunctions.transcript_per_second = (
                utils.average_runs(
                    lambda:
                        benchmark.benchmark_transcript(
                            size=self.num_of_cities
                        ),
                    self.runs
                )
            )

            completed_benchmarks += 1

            # -----------------------------------------------------
            # Hash-chain validation
            # -----------------------------------------------------

            benchmark_progress(
                completed_benchmarks,
                total_benchmarks,
                "Benchmarking transcript hash validation..."
            )

            MainFunctions.hash_validation_per_second = (
                utils.average_runs(
                    lambda:
                        benchmark.benchmark_hash_validation(
                            size=self.num_of_cities
                        ),
                    self.runs
                )
            )

            completed_benchmarks += 1

            # -----------------------------------------------------
            # COMPLETE SEMANTIC B&B REPLAY
            # -----------------------------------------------------

            benchmark_progress(
                completed_benchmarks,
                total_benchmarks,
                "Benchmarking Proof semantic validation..."
            )

            MainFunctions.semantic_validation_per_second = (
                utils.average_runs(
                    lambda:
                        benchmark.benchmark_semantic_validation(
                            size=self.num_of_cities
                        ),
                    self.runs
                )
            )

            completed_benchmarks += 1

        # =========================================================
        # FINISH
        # =========================================================

        benchmark_progress(
            completed_benchmarks,
            total_benchmarks,
            "Benchmarks complete."
        )

        MainFunctions.benchmarks_done = True

        MainFunctions.benchmarked_validation_mode = (
            self.validation_mode
        )

        MainFunctions.benchmarked_num_of_cities = (
            self.num_of_cities
        )

        # =========================================================
        # DEBUG
        # =========================================================

        print(
            "\n================ BENCHMARK RESULTS ================"
        )

        print(
            "PoW:",
            MainFunctions.hashes_per_second,
            "hashes/s"
        )

        print(
            "PoUW:",
            MainFunctions.computations_per_second,
            "B&B nodes/s"
        )

        if self.validation_mode & COUNCIL_VALIDATION:

            print(
                "Council initial:",
                MainFunctions.initial_validations_per_second,
                "validations/s"
            )

            print(
                "Council branch:",
                MainFunctions.branch_validation_nodes_per_second,
                "B&B validation nodes/s"
            )

        if self.validation_mode & PROOF_VALIDATION:

            print(
                "Proof transcript generation:",
                MainFunctions.transcript_per_second,
                "records/s"
            )

            print(
                "Proof hash validation:",
                MainFunctions.hash_validation_per_second,
                "checks/s"
            )

            print(
                "Proof semantic validation:",
                MainFunctions.semantic_validation_per_second,
                "semantic units/s"
            )

        print(
            "===================================================\n"
        )

    # Create the nodes used by the simulation.
    def create_nodes(self):
        # Generate the TSP problem shared by all nodes.
        Node.initialize_tsp(
            self.num_of_cities
        )

        Node.transcript = None
        # Create the shared transcript when proof validation is enabled.
        if self.validation_mode & PROOF_VALIDATION:

            # Generate a random 32-byte value to initialize the transcript.
            self.transcript_sigma = secrets.token_bytes(32)

            # Create the hash of the initial transcript state.
            root = Node.tsp.tsp_root

            root_children = []

            for neighbour in range(root.size):

                if (root.matrix[root.vertex][neighbour] == utils.inf):
                    continue

                if neighbour in root.path:
                    continue

                child = TspFunction._create_child(
                    root,
                    Node.tsp.matrix,
                    root.vertex,
                    neighbour
                )

                edge_cost = Node.tsp.matrix[
                root.vertex][neighbour]

                reduced_edge_cost = root.matrix[
                    root.vertex][neighbour]

                reduction_cost = (
                    child.cost
                    - root.cost
                    -reduced_edge_cost
                )

                root_children.append({
                    "selected_neighbour": neighbour,
                    "child_path": child.path[:],
                    "edge_cost": edge_cost,
                    "reduction_cost": reduction_cost,
                    "child_lower_bound": child.cost
                })

            root_data = {
                "path": root.path[:],
                "vertex": root.vertex,
                "visited": root.visited,
                "lower_bound": root.cost,
                "children": root_children
            }

            self.transcript_root = utils.create_hash(
                self.transcript_sigma.hex()
                + str(root_data)
                + str(Node.tsp.matrix)
            )

            Node.initialize_transcript(root_data, self.transcript_root)

        # Create the configured number of nodes.
        self.node_list = []

        for i in range(self.num_of_nodes):
            node = Node(
                f"node{i + 1}"
            )

            self.node_list.append(node)

        
        if all(node.search_rate <= 0 for node in self.node_list):
            raise RuntimeError("All PoUW search rates are zero")

    # Run the Proof-of-Work simulation.
    def multiple_node_pow(
        self,
        block_hash_difficulty
    ):
        # Create one worker process for each simulated node.
        with multiprocessing.Pool(
            processes=len(self.node_list)
        ) as pool:

            # Continue mining until one node finds a valid hash.
            while not Node.found:

                # Prepare the current mining state of every node.
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
                        node.blockData.transactions
                    )
                    for node in self.node_list
                ]

                # Run one mining interval for every node in parallel.
                results = pool.map(
                    powWorker.pow_worker,
                    arguments
                )

                # Find all nodes that found a valid hash
                # during the current mining interval.
                successful_nodes = [
                    (index, result)
                    for index, result in enumerate(results)
                    if result["found"]
                ]

                # If no node found a valid hash, one simulated
                # second of mining has elapsed.
                if not successful_nodes:
                    for node, result in zip(self.node_list, results):
                        node.update_pow_state(result)

                    Node.simulation_time += 1
                    continue

                # Earliest exact rational completion time; list index breaks ties.
                winner_index, winner = min(
                    successful_nodes,
                    key=lambda item: (Fraction(item[1]["hashes"],
                                               self.node_list[item[0]].hash_rate), item[0])
                )

                finishing_node = (
                    self.node_list[winner_index]
                )

                # Get the number of hashes needed by the winner
                # during the final mining interval.
                hashes = winner["hashes"]

                # Calculate the fraction of a second needed
                # by the winner to find the valid hash.
                cutoff = Fraction(hashes, finishing_node.hash_rate)
                winner_time = float(cutoff)

                # Count completed hashes, never rounded partial attempts.
                # Reconstruct each node's next nonce at exactly this cutoff.
                for node in self.node_list:
                    work_done = (node.hash_rate * cutoff.numerator) // cutoff.denominator
                    node.mining_count += work_done
                    powWorker.advance_state(node, work_done)

                finishing_node.header_hash = winner["header_hash"]

                # Advance the simulation time by the fraction
                # of a second required to find the winning hash.
                Node.simulation_time += winner_time

                # Mark the simulation as finished.
                Node.found = True

                # Calculate the total number of hashes performed
                # by all nodes during the simulation.
                total_mining_count = sum(
                    node.mining_count
                    for node in self.node_list
                )

                pow_work = (
                    total_mining_count 
                    / MainFunctions.hashes_per_second
                )

                print(
                    "TOTAL HASH RATE:",
                    sum(node.hash_rate for node in self.node_list)
                )

                print(
                    "POW OBSERVED RATE:",
                    total_mining_count / Node.simulation_time
                )

                # Return the simulation results to the benchmark
                # and GUI layers.
                return {
                    "total_hashes":
                        total_mining_count,

                    "compute_work":
                        pow_work,

                    "simulation_time":
                        Node.simulation_time,

                    "winner": {
                        "name":
                            finishing_node.name,

                        "hashes":
                            winner["hashes"],

                        "nonce":
                            winner["nonce"],

                        "extra_nonce":
                            winner["extra_nonce"],

                        "header_hash":
                            winner["header_hash"]
                    },

                    "nodes": {
                        node.name: {
                            "hash_rate":
                                node.hash_rate,

                            "hashes":
                                node.mining_count
                        }
                        for node in self.node_list
                    }
                }

    def multiple_node_pouw_tsp(self):

        if all(
            node.search_rate <= 0
            for node in self.node_list
        ):
            raise RuntimeError(
                "All PoUW search rates are zero"
            )

        # ----------------------------------------------------------
        # PoUW simulation time
        # ----------------------------------------------------------

        pouw_time = 0.0

        # ----------------------------------------------------------
        # Validation values
        # ----------------------------------------------------------

        validation_time = 0.0
        validation_valid = True

        # Normalized validation work measured in
        # reference-machine compute seconds.
        validation_compute_work = 0.0

        # ----------------------------------------------------------
        # Council Validation values
        # ----------------------------------------------------------

        council_initial_validations = 0
        council_branch_validation_nodes = 0

        council_initial_compute_work = 0.0
        council_branch_compute_work = 0.0
        council_compute_work = 0.0

        search_result = run_search(
            Node.tsp, self.node_list, Node.transcript,
            Node.transcript_pouw_ratio
        )
        pouw_time = search_result["time"]
        finishing_node = search_result["finishing_node"]
        discovering_node = search_result["discovering_node"]
        transcript_records = search_result["transcript_records"]
        Node.found = True
        Node.simulation_time = pouw_time

        # ----------------------------------------------------------
        # Display TSP result
        # ----------------------------------------------------------

        print(
            "TSP Matrix",
            Node.tsp.matrix
        )

        print(
            "Best TSP path:",
            Node.tsp.best_path
        )

        print(
            "Best TSP cost:",
            Node.tsp.best_cost
        )

        # ----------------------------------------------------------
        # Winning search node
        # ----------------------------------------------------------

        winning_node = (
            self.node_list[0]
            .tsp
            .best_node
        )

        # ==========================================================
        # RAW POUW COMPUTATIONS
        # ==========================================================

        pouw_computations = sum(
            node.computations
            for node in self.node_list
        )

        # ----------------------------------------------------------
        # Search + transcript reference-machine compute work
        # ----------------------------------------------------------
        #
        # B&B nodes
        # ----------------
        # B&B nodes / sec
        #
        # = reference seconds
        # ----------------------------------------------------------

        search_compute_work = (
            pouw_computations / MainFunctions.computations_per_second
        )
        transcript_compute_work = (
            transcript_records / MainFunctions.transcript_per_second
            if transcript_records else 0.0
        )
        pouw_compute_work = search_compute_work + transcript_compute_work
        proof_hash_checks = proof_semantic_checks = 0
        proof_hash_compute_work = proof_semantic_compute_work = 0.0

        # ----------------------------------------------------------
        # Diagnostics
        # ----------------------------------------------------------

        total_search_rate = sum(
            node.search_rate
            for node in self.node_list
        )

        print(
            "POUW COMPUTATIONS:",
            pouw_computations
        )

        print(
            "POUW TIME:",
            pouw_time
        )

        print(
            "THEORETICAL TIME:",
            pouw_computations
            / total_search_rate
        )

        print(
            "TOTAL SEARCH RATE:",
            total_search_rate
        )

        print(
            "POUW OBSERVED RATE:",
            pouw_computations
            / pouw_time
        )

        # ==========================================================
        # PROOF VALIDATION
        # ==========================================================
        #
        # Hash checks and semantic units use separate measured rates.
        # ==========================================================

        if self.validation_mode & PROOF_VALIDATION:

            validators = [
                node
                for node in self.node_list
                if node is not finishing_node
            ]

            proof_result = proof_based_validation(
                self.node_list[0].tsp,
                self.node_list[0].tsp.best_path,
                self.node_list[0].tsp.best_cost,
                Node.transcript,
                validators,
                self.transcript_sigma,
                self.transcript_root
            )

            validation_valid = (
                validation_valid
                and proof_result["valid"]
            )

            validation_time += (
                proof_result["validation_time"]
            )

            proof_hash_checks = proof_result["hash_checks"]
            proof_semantic_checks = proof_result["semantic_checks"]
            proof_hash_compute_work = (
                proof_result["hash_checks"]
                / MainFunctions.hash_validation_per_second
            )

            proof_semantic_compute_work = (
                proof_result["semantic_checks"]
                / MainFunctions.semantic_validation_per_second
            )

            proof_compute_work = (
                proof_hash_compute_work
                + proof_semantic_compute_work
            )

            validation_compute_work += (
                proof_compute_work
            )

            print(
                "\n================ PROOF VALIDATION DEBUG ================"
            )

            print(
                "Proof valid:",
                proof_result["valid"]
            )

            print(
                "Hash checks:",
                proof_result["hash_checks"]
            )

            print(
                "Hash benchmark rate:",
                MainFunctions.hash_validation_per_second,
                "checks/s"
            )

            print(
                "Hash compute work:",
                proof_hash_compute_work,
                "reference s"
            )

            print(
                "Semantic checks:",
                proof_result["semantic_checks"]
            )

            print(
                "Semantic benchmark rate:",
                MainFunctions.semantic_validation_per_second,
                "semantic units/s"
            )

            print(
                "Semantic compute work:",
                proof_semantic_compute_work,
                "reference s"
            )

            print(
                "Total Proof compute work:",
                proof_compute_work,
                "reference s"
            )

            print(
                "Proof validation time:",
                proof_result["validation_time"],
                "simulated s"
            )

            print(
                "========================================================\n"
            )


        # ==========================================================
        # COUNCIL VALIDATION
        # ==========================================================

        if self.validation_mode & COUNCIL_VALIDATION:

            council = [
                node
                for node in self.node_list
                if node is not finishing_node
            ]

            council_result = (
                council_validation(
                    self.node_list[0].tsp,
                    council,
                    self.node_list[0].tsp.best_path,
                    self.node_list[0].tsp.best_cost,
                    MainFunctions.initial_validations_per_second,
                    MainFunctions.branch_validation_nodes_per_second
                )
            )

            print("\n================ COUNCIL VALIDATION DEBUG ================")

            print(
                "Council valid:",
                council_result["valid"]
            )

            print(
                "Initial validations:",
                council_result["initial_validations"]
            )

            print(
                "Initial benchmark rate:",
                MainFunctions.initial_validations_per_second,
                "validations/s"
            )

            print(
                "Initial compute work:",
                council_result["initial_compute_work"],
                "reference s"
            )

            print(
                "Expected initial compute work:",
                (
                    council_result["initial_validations"]
                    / MainFunctions.initial_validations_per_second
                ),
                "reference s"
            )

            print(
                "Branch validation nodes:",
                council_result["branch_validation_nodes"]
            )

            print(
                "Branch benchmark rate:",
                MainFunctions.branch_validation_nodes_per_second,
                "B&B validation nodes/s"
            )

            print(
                "Branch compute work:",
                council_result["branch_compute_work"],
                "reference s"
            )

            print(
                "Expected branch compute work:",
                (
                    council_result["branch_validation_nodes"]
                    / MainFunctions.branch_validation_nodes_per_second
                ),
                "reference s"
            )

            print(
                "Total Council compute work:",
                council_result["compute_work"],
                "reference s"
            )

            print(
                "Expected total Council compute work:",
                (
                    council_result["initial_compute_work"]
                    + council_result["branch_compute_work"]
                ),
                "reference s"
            )

            print(
                "Council validation time:",
                council_result["validation_time"],
                "simulated s"
            )

            print("==========================================================\n")

            # ------------------------------------------------------
            # Validation result
            # ------------------------------------------------------

            validation_valid = (
                validation_valid
                and council_result["valid"]
            )

            # ------------------------------------------------------
            # Simulated validation time
            # ------------------------------------------------------

            validation_time += (
                council_result[
                    "validation_time"
                ]
            )

            # ------------------------------------------------------
            # Raw Council units
            # ------------------------------------------------------

            council_initial_validations = (
                council_result[
                    "initial_validations"
                ]
            )

            council_branch_validation_nodes = (
                council_result[
                    "branch_validation_nodes"
                ]
            )

            # ------------------------------------------------------
            # Normalized Council work
            # ------------------------------------------------------

            council_initial_compute_work = (
                council_result[
                    "initial_compute_work"
                ]
            )

            council_branch_compute_work = (
                council_result[
                    "branch_compute_work"
                ]
            )

            council_compute_work = (
                council_result[
                    "compute_work"
                ]
            )

            validation_compute_work += (
                council_compute_work
            )

        # ==========================================================
        # VALIDATION B&B-EQUIVALENT COMPUTATIONS
        # ==========================================================
        #
        # run_simulation() expects a validation_computations field.
        #
        # We therefore convert normalized validation work back
        # into the equivalent number of PoUW B&B computations:
        #
        # reference seconds
        # *
        # PoUW B&B nodes / reference second
        #
        # = B&B-equivalent computations
        # ----------------------------------------------------------

        validation_computations = (
            validation_compute_work
            * MainFunctions.computations_per_second
        )

        # ==========================================================
        # VALIDATED POUW COMPUTATIONS
        # ==========================================================
        #
        # Both values are now expressed in B&B-equivalent units.
        # ----------------------------------------------------------

        total_computations = (
            pouw_compute_work * MainFunctions.computations_per_second
            + validation_computations
        )

        # ==========================================================
        # TOTAL REFERENCE COMPUTE WORK
        # ==========================================================

        total_compute_work = (
            pouw_compute_work
            + validation_compute_work
        )

        # ==========================================================
        # TOTAL SIMULATED TIME
        # ==========================================================

        total_time = (
            pouw_time
            + validation_time
        )

        Node.simulation_time = (
            total_time
        )

        # ==========================================================
        # RETURN RESULTS
        # ==========================================================

        return {

            # ------------------------------------------------------
            # PoUW only
            # ------------------------------------------------------

            "pouw_computations":
                pouw_computations,
            "search_compute_work": search_compute_work,
            "transcript_records": transcript_records,
            "transcript_compute_work": transcript_compute_work,
            "proof_hash_checks": proof_hash_checks,
            "proof_semantic_checks": proof_semantic_checks,
            "proof_hash_compute_work": proof_hash_compute_work,
            "proof_semantic_compute_work": proof_semantic_compute_work,
            "finishing_node": finishing_node.name,
            "discovering_node": discovering_node.name,


            "pouw_compute_work":
                pouw_compute_work,

            "pouw_time":
                pouw_time,

            # ------------------------------------------------------
            # Validation
            # ------------------------------------------------------

            # B&B-equivalent validation computations.
            "validation_computations":
                validation_computations,

            # Correct normalized reference-machine work.
            "validation_compute_work":
                validation_compute_work,

            "validation_time":
                validation_time,

            "validation_valid":
                validation_valid,

            # ------------------------------------------------------
            # Validated PoUW
            # ------------------------------------------------------

            # B&B-equivalent search, transcript and validation work.
            "total_computations":
                total_computations,

            "total_compute_work":
                total_compute_work,

            "total_time":
                total_time,

            "simulation_time":
                total_time,

            # ------------------------------------------------------
            # Council details
            # ------------------------------------------------------

            "council_initial_validations":
                council_initial_validations,

            "council_branch_validation_nodes":
                council_branch_validation_nodes,

            "council_initial_compute_work":
                council_initial_compute_work,

            "council_branch_compute_work":
                council_branch_compute_work,

            "council_compute_work":
                council_compute_work,

            # ------------------------------------------------------
            # Winner
            # ------------------------------------------------------

            "winner": {

                "name":
                    discovering_node.name,

                "path":
                    Node.tsp.best_path[:],

                "cost":
                    Node.tsp.best_cost,

                "total_cost":
                    Node.tsp.best_cost,

                "vertex":
                    Node.tsp.best_path[-1],

                "visited":
                    Node.tsp.size,
                "lower_bound": winning_node.cost,
                "partial_path_cost": winning_node.total_cost
            },

            # ------------------------------------------------------
            # Node information
            # ------------------------------------------------------

            "nodes": {

                node.name: {

                    "hash_rate":
                        node.hash_rate,

                    "search_rate":
                        node.search_rate,

                    "computations":
                        node.computations

                }

                for node in self.node_list
            }
        }


    def run_simulation(self, progress_callback=None):

        # ---------------------------------------------------------
        # Progress tracking
        # ---------------------------------------------------------

        total_runs = self.runs * 2
        completed_runs = 0

        def update_progress():

            nonlocal completed_runs

            completed_runs += 1

            if progress_callback is not None:

                progress_callback(
                    completed_runs,
                    total_runs
                )

        # =========================================================
        # POW SIMULATIONS
        # =========================================================

        pow_results = []

        for i in range(self.runs):

            self.reset_simulation()

            result = self.multiple_node_pow(
                self.block_hash_difficulty
            )

            pow_results.append(result)

            update_progress()

        # =========================================================
        # POUW SIMULATIONS
        # =========================================================

        pouw_results = []

        for i in range(self.runs):

            self.reset_simulation()

            result = self.multiple_node_pouw_tsp()

            if (
                self.validation_mode != NO_VALIDATION
                and not result["validation_valid"]
            ):

                raise RuntimeError(
                    "PoUW solution failed validation and was rejected."
                )

            pouw_results.append(result)

            update_progress()

        # =========================================================
        # RAW WORK AVERAGES
        # =========================================================

        average_hashes = (
            sum(
                result["total_hashes"]
                for result in pow_results
            )
            / len(pow_results)
        )

        average_computations = (
            sum(
                result["pouw_computations"]
                for result in pouw_results
            )
            / len(pouw_results)
        )

        # =========================================================
        # REFERENCE COMPUTE WORK
        # =========================================================

        average_pow_compute_work = (
            sum(
                result["compute_work"]
                for result in pow_results
            )
            / len(pow_results)
        )

        average_pouw_compute_work = (
            sum(
                result["pouw_compute_work"]
                for result in pouw_results
            )
            / len(pouw_results)
        )

        average_validation_compute_work = (
            sum(
                result["validation_compute_work"]
                for result in pouw_results
            )
            / len(pouw_results)
        )

        average_validated_pouw_compute_work = (
            sum(
                result["total_compute_work"]
                for result in pouw_results
            )
            / len(pouw_results)
        )

        # =========================================================
        # SIMULATED TIME
        # =========================================================

        average_pow_simulation_time = (
            sum(
                result["simulation_time"]
                for result in pow_results
            )
            / len(pow_results)
        )

        average_pouw_simulation_time = (
            sum(
                result["pouw_time"]
                for result in pouw_results
            )
            / len(pouw_results)
        )

        average_validation_time = (
            sum(
                result["validation_time"]
                for result in pouw_results
            )
            / len(pouw_results)
        )

        average_validated_pouw_simulation_time = (
            sum(
                result["total_time"]
                for result in pouw_results
            )
            / len(pouw_results)
        )

        # =========================================================
        # NODE RATE AVERAGES
        # =========================================================

        average_pow_hash_rate = {}

        for node_name in pow_results[0]["nodes"]:

            average_pow_hash_rate[node_name] = (
                sum(
                    run["nodes"][node_name]["hash_rate"]
                    for run in pow_results
                )
                / len(pow_results)
            )

        average_pouw_hash_rate = {}

        for node_name in pouw_results[0]["nodes"]:

            average_pouw_hash_rate[node_name] = (
                sum(
                    run["nodes"][node_name]["hash_rate"]
                    for run in pouw_results
                )
                / len(pouw_results)
            )

        average_pouw_search_rate = {}

        for node_name in pouw_results[0]["nodes"]:

            average_pouw_search_rate[node_name] = (
                sum(
                    run["nodes"][node_name]["search_rate"]
                    for run in pouw_results
                )
                / len(pouw_results)
            )

        # =========================================================
        # RAW NODE WORK AVERAGES
        # =========================================================

        average_pow_mining_count = {}

        for node_name in pow_results[0]["nodes"]:

            average_pow_mining_count[node_name] = (
                sum(
                    run["nodes"][node_name]["hashes"]
                    for run in pow_results
                )
                / len(pow_results)
            )

        average_pouw_computations = {}

        for node_name in pouw_results[0]["nodes"]:

            average_pouw_computations[node_name] = (
                sum(
                    run["nodes"][node_name]["computations"]
                    for run in pouw_results
                )
                / len(pouw_results)
            )

        # =========================================================
        # DEBUG / CONSISTENCY CHECKS
        # =========================================================

        print("\n================ SIMULATION AVERAGES ================")

        print(
            "AVG POW RAW HASHES:",
            average_hashes
        )

        print(
            "AVG POUW RAW B&B NODES:",
            average_computations
        )

        print(
            "AVG POW REFERENCE WORK:",
            average_pow_compute_work
        )

        print(
            "AVG POUW REFERENCE WORK:",
            average_pouw_compute_work
        )

        print(
            "AVG VALIDATION REFERENCE WORK:",
            average_validation_compute_work
        )

        print(
            "AVG VALIDATED POUW REFERENCE WORK:",
            average_validated_pouw_compute_work
        )

        print(
            "EXPECTED VALIDATED WORK:",
            (
                average_pouw_compute_work
                + average_validation_compute_work
            )
        )

        print(
            "VALIDATED WORK ERROR:",
            abs(
                average_validated_pouw_compute_work
                - (
                    average_pouw_compute_work
                    + average_validation_compute_work
                )
            )
        )

        print(
            "AVG POW TIME:",
            average_pow_simulation_time
        )

        print(
            "AVG POUW TIME:",
            average_pouw_simulation_time
        )

        print(
            "AVG VALIDATION TIME:",
            average_validation_time
        )

        print(
            "AVG VALIDATED POUW TIME:",
            average_validated_pouw_simulation_time
        )

        print(
            "EXPECTED VALIDATED TIME:",
            (
                average_pouw_simulation_time
                + average_validation_time
            )
        )

        print(
            "VALIDATED TIME ERROR:",
            abs(
                average_validated_pouw_simulation_time
                - (
                    average_pouw_simulation_time
                    + average_validation_time
                )
            )
        )

        print("=====================================================\n")

        # =========================================================
        # RETURN
        # =========================================================

        return {

            # -----------------------------------------------------
            # Raw totals
            # -----------------------------------------------------

            "average_hashes":
                average_hashes,

            "average_computations":
                average_computations,

            # -----------------------------------------------------
            # Comparable normalized work
            # -----------------------------------------------------

            "average_pow_compute_work":
                average_pow_compute_work,

            "average_pouw_compute_work":
                average_pouw_compute_work,

            "average_validation_compute_work":
                average_validation_compute_work,

            "average_validated_pouw_compute_work":
                average_validated_pouw_compute_work,

            # -----------------------------------------------------
            # Simulated time
            # -----------------------------------------------------

            "average_pow_simulation_time":
                average_pow_simulation_time,

            "average_pouw_simulation_time":
                average_pouw_simulation_time,

            "average_validation_time":
                average_validation_time,

            "average_validated_pouw_simulation_time":
                average_validated_pouw_simulation_time,

            # -----------------------------------------------------
            # PoW details
            # -----------------------------------------------------

            "pow": {

                "average_hash_rate":
                    average_pow_hash_rate,

                "average_mining_count":
                    average_pow_mining_count,

                "runs":
                    pow_results
            },

            # -----------------------------------------------------
            # PoUW details
            # -----------------------------------------------------

            "pouw": {

                "average_hash_rate":
                    average_pouw_hash_rate,

                "average_search_rate":
                    average_pouw_search_rate,

                "average_computations":
                    average_pouw_computations,

                "average_compute_work":
                    average_pouw_compute_work,

                "average_simulation_time":
                    average_pouw_simulation_time,

                "runs":
                    pouw_results
            },

            # -----------------------------------------------------
            # Validated PoUW details
            # -----------------------------------------------------

            "validated_pouw": {

                "average_compute_work":
                    average_validated_pouw_compute_work,

                "average_validation_compute_work":
                    average_validation_compute_work,

                "average_simulation_time":
                    average_validated_pouw_simulation_time,

                "average_validation_time":
                    average_validation_time,

                "runs":
                    pouw_results
            }
        }
        
    def reset_simulation(self):

        # Create a fresh block.
        Node.blockData = BlockData()

        # Reset shared simulation state.
        Node.found = False
        Node.simulation_time = 0.0

        # Always discard any transcript from a previous run.
        Node.transcript = None

        # Recreate nodes and generate a fresh TSP instance.
        # Benchmarks are intentionally reused.
        self.create_nodes()