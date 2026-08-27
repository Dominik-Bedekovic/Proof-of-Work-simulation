from nodes import Node

import powWorker
import utils
import benchmark
import multiprocessing

from blockData import BlockData

from validation import council_validation
from validation import proof_based_validation


# ---------------------------------------------------------
# Validation modes
# ---------------------------------------------------------

NO_VALIDATION = 0b00
PROOF_VALIDATION = 0b01
COUNCIL_VALIDATION = 0b10



class MainFunctions:

    benchmarks_done = False

    def __init__(
        self,
        num_of_nodes,
        num_of_cities,
        runs,
        block_hash_difficulty,
        validation_mode,
    ):

        # -------------------------------------------------
        # Reset shared ratios.
        # -------------------------------------------------

        Node.pouw_pow_ratio = 0
        Node.validation_pow_ratio = 0
        Node.transcript_pouw_ratio = 0
        Node.path_validation_pow_ratio = 0
        Node.hash_validation_pow_ratio = 0

        # -------------------------------------------------
        # Store simulation parameters.
        # -------------------------------------------------

        self.num_of_nodes = num_of_nodes
        self.num_of_cities = num_of_cities
        self.runs = runs
        self.block_hash_difficulty = block_hash_difficulty
        self.validation_mode = validation_mode

        # -------------------------------------------------
        # Run benchmarks once.
        #
        # These values are then reused by every simulation
        # run. We do NOT benchmark again when reset_simulation()
        # is called.
        # -------------------------------------------------

        if not MainFunctions.benchmarks_done:
            self.run_benchmarks()

        # -------------------------------------------------
        # Create nodes.
        # -------------------------------------------------

        self.create_nodes()

    def run_benchmarks(self):

        print("\n========================================")
        print("Running benchmarks")
        print("========================================\n")

        MainFunctions.hashes_per_second = (
            utils.average_runs(
                benchmark.benchmark_pow,
                self.runs
            )
        )

        print("PoW Benchmark:")
        print(
            f"Hashes/sec: "
            f"{MainFunctions.hashes_per_second:.0f}\n"
        )

        MainFunctions.computations_per_second = (
            utils.average_runs(
                lambda: benchmark.benchmark_tsp_pouw(
                    size=self.num_of_cities
                ),
                self.runs
            )
        )

        print("PoUW TSP Benchmark:")
        print(
            f"Computations/sec: "
            f"{MainFunctions.computations_per_second:.0f}\n"
        )

        # ---------------------------------------------
        # PoUW / PoW ratio
        # ---------------------------------------------

        Node.pouw_pow_ratio = (
            MainFunctions.computations_per_second
            / MainFunctions.hashes_per_second
        )

        print(
            f"PoUW/PoW ratio: "
            f"{Node.pouw_pow_ratio:.6f}\n"
        )

        # ---------------------------------------------
        # Council validation
        # ---------------------------------------------

        if self.validation_mode & COUNCIL_VALIDATION:
            MainFunctions.validations_per_second = (
                utils.average_runs(
                    lambda: benchmark.benchmark_validation(
                        size=self.num_of_cities
                    ),
                    self.runs
                )
            )

            Node.validation_pow_ratio = (
                MainFunctions.validations_per_second
                / MainFunctions.hashes_per_second
            )

            print("Council Validation Benchmark:")
            print(
                f"Validations/sec: "
                f"{MainFunctions.validations_per_second:.0f}"
            )

            print(
                f"Validation/PoW ratio: "
                f"{Node.validation_pow_ratio:.6f}\n"
            )

        # ---------------------------------------------
        # Transcript
        # ---------------------------------------------

        if self.validation_mode & PROOF_VALIDATION:
            MainFunctions.transcript_per_second = (
                utils.average_runs(
                    benchmark.benchmark_transcript,
                    self.runs
                )
            )

            Node.transcript_pouw_ratio = (
                MainFunctions.transcript_per_second
                / MainFunctions.computations_per_second
            )

            print("Transcript Benchmark:")
            print(
                f"Transcript steps/sec: "
                f"{MainFunctions.transcript_per_second:.0f}"
            )

            print(
                f"Transcript/PoUW ratio: "
                f"{Node.transcript_pouw_ratio:.6f}\n"
            )

        # ---------------------------------------------
        # Path validation
        # ---------------------------------------------

            MainFunctions.path_validation_per_second = (
                utils.average_runs(
                    lambda: benchmark.benchmark_path_validation(
                        size=self.num_of_cities
                    ),
                    self.runs
                )
            )

            Node.path_validation_pow_ratio = (
                MainFunctions.path_validation_per_second
                / MainFunctions.hashes_per_second
            )

            print("Path Validation Benchmark:")
            print(
                f"Validations/sec: "
                f"{MainFunctions.path_validation_per_second:.0f}"
            )

            print(
                f"Path validation/PoW ratio: "
                f"{Node.path_validation_pow_ratio:.6f}\n"
            )

        # ---------------------------------------------
        # Hash validation
        # ---------------------------------------------

            MainFunctions.hash_validation_per_second = (
                utils.average_runs(
                    lambda: benchmark.benchmark_hash_validation(
                        steps=1000
                    ),
                    self.runs
                )
            )

            Node.hash_validation_pow_ratio = (
                MainFunctions.hash_validation_per_second
                / MainFunctions.hashes_per_second
            )

            print("Hash Validation Benchmark:")
            print(
                f"Steps/sec: "
                f"{MainFunctions.hash_validation_per_second:.0f}"
            )

            print(
                f"Hash validation/PoW ratio: "
                f"{Node.hash_validation_pow_ratio:.6f}\n"
            )

            MainFunctions.benchmarks_done = True

        print("========================================")
        print("Benchmarks complete")
        print("========================================\n")

    # =====================================================
    # CREATE NODES
    # =====================================================

    def create_nodes(self):

        # ---------------------------------------------
        # Generate the shared TSP problem.
        # ---------------------------------------------

        Node.initialize_tsp(
            self.num_of_cities
        )

        # ---------------------------------------------
        # Create transcript if proof validation is used.
        # ---------------------------------------------

        if self.validation_mode & PROOF_VALIDATION:
            Node.initialize_transcript()

        # ---------------------------------------------
        # Create nodes.
        # ---------------------------------------------

        self.node_list = []

        for i in range(self.num_of_nodes):

            node = Node(
                f"node{i + 1}"
            )

            self.node_list.append(node)


    # =====================================================
    # PROOF OF WORK
    # =====================================================

    def multiple_node_pow(
        self,
        block_hash_difficulty
    ):

        print("PoW simulation:\n")

        print("Hash rate:")

        for node in self.node_list:

            print(
                f"{node.name}: {node.hash_rate}",
                end="\t"
            )

        print("\n")

        with multiprocessing.Pool(
            processes=len(self.node_list)
        ) as pool:

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
                        node.blockData.transactions
                    )

                    for node in self.node_list
                ]

                results = pool.map(
                    powWorker.pow_worker,
                    arguments
                )

                # -----------------------------------------
                # Update nodes.
                # -----------------------------------------

                for node, result in zip(
                    self.node_list,
                    results
                ):

                    if not result["found"]:

                        node.nonce = result["nonce"]

                        node.coinbase["extra_nonce"] = (
                            result["extra_nonce"]
                        )

                        node.merkle_root = (
                            result["merkle_root"]
                        )

                # -----------------------------------------
                # Find successful workers.
                # -----------------------------------------

                successful_nodes = [

                    (index, result)

                    for index, result in enumerate(results)

                    if result["found"]
                ]

                if not successful_nodes:

                    for node in self.node_list:

                        node.mining_count += (
                            node.hash_rate
                        )

                    Node.simulation_time += 1

                    continue

                # -----------------------------------------
                # Winning node.
                # -----------------------------------------

                winner_index, winner = (
                    successful_nodes[0]
                )

                finishing_node = (
                    self.node_list[winner_index]
                )

                hashes = winner["hashes"]

                # -----------------------------------------
                # Fraction of final second.
                # -----------------------------------------

                winner_time = (
                    hashes
                    / finishing_node.hash_rate
                )

                # -----------------------------------------
                # Count work performed by every node.
                # -----------------------------------------

                for node in self.node_list:

                    work_done = round(
                        node.hash_rate
                        * winner_time
                    )

                    node.mining_count += work_done

                # -----------------------------------------
                # Save winning state.
                # -----------------------------------------

                finishing_node.nonce = (
                    winner["nonce"]
                )

                finishing_node.coinbase["extra_nonce"] = (
                    winner["extra_nonce"]
                )

                finishing_node.merkle_root = (
                    winner["merkle_root"]
                )

                finishing_node.header_hash = (
                    winner["header_hash"]
                )

                # -----------------------------------------
                # Update simulation state.
                # -----------------------------------------

                Node.simulation_time += (
                    winner_time
                )

                Node.found = True

                # -----------------------------------------
                # Output.
                # -----------------------------------------

                print(
                    "\nFinishing node:",
                    finishing_node.name
                )

                print(
                    "Hashes:",
                    hashes
                )

                print(
                    "Nonce:",
                    winner["nonce"]
                )

                print(
                    "Extra nonce:",
                    winner["extra_nonce"]
                )

                print(
                    "Hash:",
                    winner["header_hash"]
                )

                print("\nMining count:")

                for node in self.node_list:

                    print(
                        f"{node.name}: "
                        f"{node.mining_count}",
                        end="\t"
                    )

                total_mining_count = sum(
                    node.mining_count
                    for node in self.node_list
                )

                print(
                    "\n\nTotal mining count:",
                    total_mining_count
                )

                print(
                    "Simulation time:",
                    Node.simulation_time
                )

                return total_mining_count


    # =====================================================
    # PROOF OF USEFUL WORK
    # =====================================================

    def multiple_node_pouw_tsp(self):

        print("PoUW TSP simulation: \n")

        print("Matrix:")

        for row in Node.tsp.matrix:
            print(row)

        print("\nSearch rate:")

        for node in self.node_list:

            print(
                f"{node.name}: "
                f"{node.search_rate}",
                end="\t"
            )

        while not Node.found:

            results = []

            # ---------------------------------------------
            # Each node performs one batch.
            # ---------------------------------------------

            for node in self.node_list:

                (
                    computations,
                    _,
                    transcript_time,
                    finished
                ) = node.pouw_mining()

                results.append(
                    (
                        computations,
                        transcript_time,
                        finished
                    )
                )

                if finished:
                    Node.found = True

            # ---------------------------------------------
            # Search finished.
            # ---------------------------------------------

            if Node.found:

                finishing_node_index = next(

                    i

                    for i, result in enumerate(results)

                    if result[2]
                )

                finishing_node = (
                    self.node_list[
                        finishing_node_index
                    ]
                )

                finishing_node_computations = (
                    results[
                        finishing_node_index
                    ][0]
                )

                # -----------------------------------------
                # Final fraction of simulation step.
                # -----------------------------------------

                winner_time = (

                    finishing_node_computations
                    / finishing_node.search_rate

                    + transcript_time
                )

                # -----------------------------------------
                # Remove unused work.
                # -----------------------------------------

                if finishing_node_computations > 0:

                    for i, node in enumerate(
                        self.node_list[:len(results)]
                    ):

                        if node is not finishing_node:

                            computation_done = (
                                results[i][0]
                            )

                            final_batch = round(

                                node.search_rate
                                * winner_time
                            )

                            node.computations -= (

                                computation_done
                                - final_batch
                            )

                Node.simulation_time += (
                    winner_time
                )

                # -----------------------------------------
                # Output.
                # -----------------------------------------

                print(
                    "\nBest path:",
                    self.node_list[0]
                    .tsp
                    .best_path
                )

                print(
                    "Best cost:",
                    self.node_list[0]
                    .tsp
                    .best_cost
                )

                winning_node = (
                    self.node_list[0]
                    .tsp
                    .best_node
                )

                print(
                    "\nWinning TSP node:"
                )

                print(
                    "Name:",
                    finishing_node.name
                )

                print(
                    "Path:",
                    winning_node.path
                )

                print(
                    "Cost:",
                    winning_node.cost
                )

                print(
                    "Total cost:",
                    winning_node.total_cost
                )

                print(
                    "Vertex:",
                    winning_node.vertex
                )

                print(
                    "Visited:",
                    winning_node.visited
                )

                print("\nComputations:")

                for node in self.node_list:

                    print(
                        f"{node.name}: "
                        f"{node.computations}",
                        end="\t"
                    )

                total_computations = sum(
                    node.computations
                    for node in self.node_list
                )

                print(
                    "\n\nTotal computations:",
                    round(total_computations)
                )

                print(
                    f"Simulation time: "
                    f"{Node.simulation_time:.2f}s"
                )

                # =========================================
                # PROOF VALIDATION
                # =========================================

                if self.validation_mode & PROOF_VALIDATION:

                    validators = [

                        node

                        for node in self.node_list

                        if node is not finishing_node
                    ]

                    (
                        proof_valid,
                        validation_computations,
                        validation_time
                    ) = proof_based_validation(

                        self.node_list[0].tsp,

                        self.node_list[0]
                        .tsp
                        .best_path,

                        self.node_list[0]
                        .tsp
                        .best_cost,

                        Node.transcript,

                        validators
                    )

                    print(
                        f"Proof validation result: "
                        f"{proof_valid}"
                    )

                    print(
                        f"Validation computations: "
                        f"{validation_computations}"
                    )

                    print(
                        f"Validation time: "
                        f"{validation_time:.4f}s"
                    )

                    total_computations += (
                        validation_computations
                    )

                    Node.simulation_time += (
                        validation_time
                    )

                # =========================================
                # COUNCIL VALIDATION
                # =========================================

                if self.validation_mode & COUNCIL_VALIDATION:

                    council = [

                        node

                        for node in self.node_list

                        if node is not finishing_node
                    ]

                    (
                        result,
                        validation_computations,
                        validation_time
                    ) = council_validation(

                        self.node_list[0]
                        .tsp,

                        council,

                        self.node_list[0]
                        .tsp
                        .best_path,

                        self.node_list[0]
                        .tsp
                        .best_cost
                    )

                    print(
                        f"Council result: "
                        f"{result}"
                    )

                    print(
                        f"Validation computations: "
                        f"{validation_computations}"
                    )

                    print(
                        f"Validation time: "
                        f"{validation_time:.4f}s"
                    )

                    total_computations += (
                        validation_computations
                    )

                    Node.simulation_time += (
                        validation_time
                    )

                # -----------------------------------------
                # Final output.
                # -----------------------------------------

                print(
                    f"\nTotal computations: "
                    f"{total_computations}"
                )

                print(
                    f"Final simulation time: "
                    f"{Node.simulation_time:.2f}s"
                )

                return total_computations

            # ---------------------------------------------
            # Search not finished.
            # ---------------------------------------------

            round_transcript_time = max(
                result[1]
                for result in results
            )

            Node.simulation_time += (
                1 + round_transcript_time
            )


    # =====================================================
    # RUN SIMULATION
    # =====================================================

    def run_simulation(self):

        # ---------------------------------------------
        # PoW run.
        # ---------------------------------------------

        def run_pow():

            self.reset_simulation()

            return self.multiple_node_pow(
                self.block_hash_difficulty
            )

        # ---------------------------------------------
        # PoUW run.
        # ---------------------------------------------

        def run_pouw():

            self.reset_simulation()

            return self.multiple_node_pouw_tsp()

        # ---------------------------------------------
        # Average PoW.
        # ---------------------------------------------

        average_hashes = utils.average_runs(
            run_pow,
            self.runs
        )

        # ---------------------------------------------
        # Average PoUW.
        # ---------------------------------------------

        average_computations = utils.average_runs(
            run_pouw,
            self.runs
        )

        print(
            f"Average hashes: "
            f"{average_hashes:.2f}"
        )

        print(
            f"Average computation: "
            f"{average_computations:.2f}"
        )

        return (
            average_hashes,
            average_computations
        )


    # =====================================================
    # RESET SIMULATION
    # =====================================================

    def reset_simulation(self):

        # ---------------------------------------------
        # Generate a new block.
        # ---------------------------------------------

        Node.blockData = BlockData()

        # ---------------------------------------------
        # Reset simulation state.
        # ---------------------------------------------

        Node.found = False

        Node.simulation_time = 0

        # ---------------------------------------------
        # Recreate nodes and the TSP problem.
        #
        # IMPORTANT:
        # This does NOT run benchmarks.
        # ---------------------------------------------

        self.create_nodes()

