from nodes import Node
import powWorker
import utils
import benchmark
import multiprocessing

from blockData import BlockData
from validation import council_validation
from validation import proof_based_validation

# Validation modes
NO_VALIDATION = 0b00
PROOF_VALIDATION = 0b01
COUNCIL_VALIDATION = 0b10


class MainFunctions:

    benchmarks_done = False
    benchmarked_validation_mode = None

    def __init__(
        self,
        num_of_nodes,
        num_of_cities,
        runs,
        block_hash_difficulty,
        validation_mode,
        benchmark_progress_callback=None
    ):
        # Reset ratios shared between nodes.
        #Node.pouw_pow_ratio = 0
        #Node.validation_pow_ratio = 0
        #Node.transcript_pouw_ratio = 0
        #Node.path_validation_pow_ratio = 0
        #Node.hash_validation_pow_ratio = 0

        # Store the simulation parameters.
        self.num_of_nodes = num_of_nodes
        self.num_of_cities = num_of_cities
        self.runs = runs
        self.block_hash_difficulty = block_hash_difficulty
        self.validation_mode = validation_mode

        # Run benchmarks only once.
        # The benchmark results are reused for subsequent simulations.
        if (
            not MainFunctions.benchmarks_done
            or MainFunctions.benchmarked_validation_mode != self.validation_mode
        ):
            self.run_benchmarks(
                progress_callback=benchmark_progress_callback
            )

        self.set_ratios()
        self.create_nodes()

    def set_ratios(self):
        Node.pouw_pow_ratio = (
            MainFunctions.computations_per_second
            / MainFunctions.hashes_per_second
        )

        Node.validation_pow_ratio = 0
        Node.transcript_pouw_ratio = 0
        Node.path_validation_pow_ratio = 0
        Node.hash_validation_pow_ratio = 0

        if self.validation_mode & COUNCIL_VALIDATION:
            Node.validation_pow_ratio = (
                MainFunctions.validations_per_second
                / MainFunctions.hashes_per_second
            )

        if self.validation_mode & PROOF_VALIDATION:
            Node.transcript_pouw_ratio = (
                MainFunctions.transcript_per_second
                / MainFunctions.computations_per_second
            )

            Node.path_validation_pow_ratio = (
                MainFunctions.path_validation_per_second
                / MainFunctions.hashes_per_second
            )

            Node.hash_validation_pow_ratio = (
                MainFunctions.hash_validation_per_second
                / MainFunctions.hashes_per_second
            )

        # Create the nodes used in the simulation.
        self.create_nodes()

        #print(
        #    "BENCHMARKS:",
        #    MainFunctions.benchmarks_done,
        #    "POUW RATIO:",
        #    Node.pouw_pow_ratio,
        #   "SEARCH RATES:",
        #    [node.search_rate for node in self.node_list],
        #    flush=True
        #)

    def run_benchmarks(self, progress_callback=None):

        def benchmark_progress(step, total, message):
            if progress_callback is not None:
                progress_callback(step, total, message)

        total_benchmarks = 2

        if self.validation_mode & COUNCIL_VALIDATION:
            total_benchmarks += 1

        if self.validation_mode & PROOF_VALIDATION:
            total_benchmarks += 3

        completed_benchmarks = 0

        # Measure the average number of SHA-256 hashes
        # that can be calculated per second.
        MainFunctions.hashes_per_second = (
            utils.average_runs(
                benchmark.benchmark_pow,
                self.runs
            )
        )

        completed_benchmarks += 1        

        # Measure the average number of TSP search
        # computations that can be performed per second.
        MainFunctions.computations_per_second = (
            utils.average_runs(
                lambda: benchmark.benchmark_tsp_pouw(
                    size=self.num_of_cities
                ),
                self.runs
            )
        )

        completed_benchmarks += 1

        # Calculate the computational ratio between PoUW and PoW.
        Node.pouw_pow_ratio = (
            MainFunctions.computations_per_second
            / MainFunctions.hashes_per_second
        )

        # Benchmark council validation when it is enabled.
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

            completed_benchmarks += 1

        # Benchmark transcript generation when proof validation is enabled.
        if self.validation_mode & PROOF_VALIDATION:
            #print("INITIALIZING PROOF VALIDATION")
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

            completed_benchmarks += 1

            # Benchmark validation of the TSP path.
            MainFunctions.path_validation_per_second = (
                utils.average_runs(
                    lambda: benchmark.benchmark_path_validation(
                        size=self.num_of_cities
                    ),
                    self.runs
                )
            )

            completed_benchmarks += 1

            Node.path_validation_pow_ratio = (
                MainFunctions.path_validation_per_second
                / MainFunctions.hashes_per_second
            )

            # Benchmark validation of the transcript hashes.
            MainFunctions.hash_validation_per_second = (
                utils.average_runs(
                    lambda: benchmark.benchmark_hash_validation(
                        steps=1000
                    ),
                    self.runs
                )
            )

            completed_benchmarks += 1

            Node.hash_validation_pow_ratio = (
                MainFunctions.hash_validation_per_second
                / MainFunctions.hashes_per_second
            )

        # Mark the benchmarks as completed so they are not repeated.
        MainFunctions.benchmarks_done = True
        MainFunctions.benchmarked_validation_mode = self.validation_mode

    # Create the nodes used by the simulation.
    def create_nodes(self):
        # Generate the TSP problem shared by all nodes.
        Node.initialize_tsp(
            self.num_of_cities
        )

        # Create the shared transcript when proof validation is enabled.
        if self.validation_mode & PROOF_VALIDATION:
            Node.initialize_transcript()

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

                # Update nodes that did not find a valid hash
                # during the current mining interval.
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
                    for node in self.node_list:
                        node.mining_count += node.hash_rate

                    Node.simulation_time += 1
                    continue

                # Select the first node that found a valid hash.
                winner_index, winner = successful_nodes[0]

                finishing_node = (
                    self.node_list[winner_index]
                )

                # Get the number of hashes needed by the winner
                # during the final mining interval.
                hashes = winner["hashes"]

                # Calculate the fraction of a second needed
                # by the winner to find the valid hash.
                winner_time = (
                    hashes
                    / finishing_node.hash_rate
                )

                # Calculate how much work every node performed
                # during the final fraction of the simulated second.
                for node in self.node_list:
                    work_done = round(
                        node.hash_rate
                        * winner_time
                    )

                    node.mining_count += work_done

                # Save the winning mining state.
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

                # Return the simulation results to the benchmark
                # and GUI layers.
                return {
                    "total_hashes":
                        total_mining_count,

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


    # Run the Proof-of-Useful-Work TSP simulation.
    def multiple_node_pouw_tsp(self):

        if all(node.search_rate <= 0 for node in self.node_list):
            raise RuntimeError("All PoUW search rates are zero")

        # Time spent performing PoUW mining.
        # This includes transcript generation because the transcript
        # is generated during the PoUW search.
        pouw_time = 0.0

        # Validation time for the selected validation method.
        validation_time = 0.0

        while not Node.found:

            results = []

            # Let every node perform one batch of TSP computations.
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

                # Stop the search when a node finds the solution.
                if finished:
                    Node.found = True

            # Check whether the search has finished.
            if Node.found:

                # Find the node that finished the search first.
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

                # Get the transcript time belonging to the
                # finishing node.
                finishing_node_transcript_time = (
                    results[
                        finishing_node_index
                    ][1]
                )

                # Calculate the final fraction of the simulation step.
                #
                # The first term represents the fraction of a second
                # required to perform the finishing node's computations.
                #
                # The second term represents the transcript generation
                # time associated with that batch.
                winner_time = (
                    finishing_node_computations
                    / finishing_node.search_rate
                    + finishing_node_transcript_time
                )

                # Remove work that would not have been performed
                # because the winning node finished before the other
                # nodes completed their current batch.
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

                # The time accumulated before the final batch.
                # winner_time represents the final partial step.
                pouw_time += winner_time

                # Keep the global simulation clock synchronized.
                Node.simulation_time += winner_time

                # Get the best TSP node found during the search.
                winning_node = (
                    self.node_list[0]
                    .tsp
                    .best_node
                )

                # Calculate the total PoUW computational work.
                pouw_computations = sum(
                    node.computations
                    for node in self.node_list
                )

                # Validation starts with zero cost.
                validation_computations = 0
                validation_time = 0.0

                # --------------------------------------------------
                # Proof validation
                # --------------------------------------------------

                if self.validation_mode & PROOF_VALIDATION:

                    validators = [
                        node
                        for node in self.node_list
                        if node is not finishing_node
                    ]

                    (
                        proof_valid,
                        proof_computations,
                        proof_time
                    ) = proof_based_validation(
                        self.node_list[0].tsp,
                        self.node_list[0].tsp.best_path,
                        self.node_list[0].tsp.best_cost,
                        Node.transcript,
                        validators
                    )

                    validation_computations += (
                        proof_computations
                    )

                    validation_time += (
                        proof_time
                    )

                # --------------------------------------------------
                # Council validation
                # --------------------------------------------------

                if self.validation_mode & COUNCIL_VALIDATION:

                    council = [
                        node
                        for node in self.node_list
                        if node is not finishing_node
                    ]

                    (
                        council_result,
                        council_computations,
                        council_time
                    ) = council_validation(
                        self.node_list[0].tsp,
                        council,
                        self.node_list[0].tsp.best_path,
                        self.node_list[0].tsp.best_cost
                    )

                    validation_computations += (
                        council_computations
                    )

                    validation_time += (
                        council_time
                    )

                # --------------------------------------------------
                # Final totals
                # --------------------------------------------------

                # Total computational work consists of:
                #
                #     PoUW work + validation work
                #
                total_computations = (
                    pouw_computations
                    + validation_computations
                )

                # Total time consists of:
                #
                #     PoUW time + validation time
                #
                # PoUW time already includes transcript generation.
                total_time = (
                    pouw_time
                    + validation_time
                )

                # Advance the global simulation clock by the
                # validation time only.
                Node.simulation_time += validation_time

                # Return the final simulation results.
                return {
                    # -----------------------------
                    # PoUW only
                    # -----------------------------

                    "pouw_computations":
                        pouw_computations,

                    "pouw_time":
                        pouw_time,

                    # -----------------------------
                    # Validation only
                    # -----------------------------

                    "validation_computations":
                        validation_computations,

                    "validation_time":
                        validation_time,

                    # -----------------------------
                    # PoUW + validation
                    # -----------------------------

                    "total_computations":
                        total_computations,

                    "total_time":
                        total_time,

                    # Keep simulation_time for compatibility
                    # with existing code.
                    "simulation_time":
                        total_time,

                    # -----------------------------
                    # Winner
                    # -----------------------------

                    "winner": {
                        "name":
                            finishing_node.name,

                        "path":
                            winning_node.path,

                        "cost":
                            winning_node.cost,

                        "total_cost":
                            winning_node.total_cost,

                        "vertex":
                            winning_node.vertex,

                        "visited":
                            winning_node.visited
                    },

                    # -----------------------------
                    # Node information
                    # -----------------------------

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

            # ------------------------------------------------------
            # Search has not finished.
            # Advance the simulation by one full second plus
            # the transcript generation time for this round.
            # ------------------------------------------------------

            round_transcript_time = max(
                result[1]
                for result in results
            )

            round_time = (
                1
                + round_transcript_time
            )

            pouw_time += round_time

            Node.simulation_time += round_time


    # Run all configured simulations and calculate their averages.
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

        # ---------------------------------------------------------
        # PoW simulations
        # ---------------------------------------------------------

        pow_results = []

        for i in range(self.runs):

            # Reset the simulation before starting a new run.
            self.reset_simulation()

            # Run PoW using the configured mining difficulty.
            result = self.multiple_node_pow(
                self.block_hash_difficulty
            )

            pow_results.append(result)

            # One simulation run has completed.
            update_progress()

        # ---------------------------------------------------------
        # PoUW simulations
        # ---------------------------------------------------------

        pouw_results = []

        for i in range(self.runs):

            # Reset the simulation before starting a new run.
            self.reset_simulation()

            # Run PoUW using the currently selected validation mode.
            result = self.multiple_node_pouw_tsp()

            pouw_results.append(result)

            # One simulation run has completed.
            update_progress()

        # ---------------------------------------------------------
        # Everything below this point is unchanged
        # ---------------------------------------------------------

        average_hashes = (
            sum(
                result["total_hashes"]
                for result in pow_results
            )
            / len(pow_results)
        )

        average_pow_simulation_time = (
            sum(
                result["simulation_time"]
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

        average_pouw_simulation_time = (
            sum(
                result["pouw_time"]
                for result in pouw_results
            )
            / len(pouw_results)
        )

        average_validation_computations = (
            sum(
                result["validation_computations"]
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

        average_validated_pouw_computations = (
            sum(
                result["total_computations"]
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

        return {

            "average_hashes":
                average_hashes,

            "average_computations":
                average_computations,

            "average_pow_simulation_time":
                average_pow_simulation_time,

            "average_pouw_simulation_time":
                average_pouw_simulation_time,

            "average_validation_computations":
                average_validation_computations,

            "average_validation_time":
                average_validation_time,

            "average_validated_pouw_computations":
                average_validated_pouw_computations,

            "average_validated_pouw_simulation_time":
                average_validated_pouw_simulation_time,

            "pow": {
                "average_hash_rate":
                    average_pow_hash_rate,

                "average_mining_count":
                    average_pow_mining_count,

                "runs":
                    pow_results
            },

            "pouw": {
                "average_hash_rate":
                    average_pouw_hash_rate,

                "average_search_rate":
                    average_pouw_search_rate,

                "average_computations":
                    average_pouw_computations,

                "runs":
                    pouw_results
            },

            "validated_pouw": {
                "average_computations":
                    average_validated_pouw_computations,

                "average_simulation_time":
                    average_validated_pouw_simulation_time,

                "average_validation_computations":
                    average_validation_computations,

                "average_validation_time":
                    average_validation_time,

                "runs":
                    pouw_results
            }
        }
    
    # Reset the simulation state before starting a new run.
    def reset_simulation(self):

        # Create a new block with fresh transactions,
        # timestamp and previous hash.
        Node.blockData = BlockData()

        # Mark the simulation as unfinished.
        Node.found = False

        # Reset the simulated time to zero.
        Node.simulation_time = 0

        if self.validation_mode & PROOF_VALIDATION:
            Node.transcript = None

        # Recreate the nodes and generate a new TSP problem.
        # Benchmarks are not run again here.
        self.create_nodes()