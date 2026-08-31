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

    def __init__(
        self,
        num_of_nodes,
        num_of_cities,
        runs,
        block_hash_difficulty,
        validation_mode,
    ):
        # Reset ratios shared between nodes.
        Node.pouw_pow_ratio = 0
        Node.validation_pow_ratio = 0
        Node.transcript_pouw_ratio = 0
        Node.path_validation_pow_ratio = 0
        Node.hash_validation_pow_ratio = 0

        # Store the simulation parameters.
        self.num_of_nodes = num_of_nodes
        self.num_of_cities = num_of_cities
        self.runs = runs
        self.block_hash_difficulty = block_hash_difficulty
        self.validation_mode = validation_mode

        # Run benchmarks only once.
        # The benchmark results are reused for subsequent simulations.
        if not MainFunctions.benchmarks_done:
            self.run_benchmarks()

        # Create the nodes used in the simulation.
        self.create_nodes()

    def run_benchmarks(self):
        # Measure the average number of SHA-256 hashes
        # that can be calculated per second.
        MainFunctions.hashes_per_second = (
            utils.average_runs(
                benchmark.benchmark_pow,
                self.runs
            )
        )

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

        # Benchmark transcript generation when proof validation is enabled.
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

            # Benchmark validation of the TSP path.
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

            # Benchmark validation of the transcript hashes.
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

        # Mark the benchmarks as completed so they are not repeated.
        MainFunctions.benchmarks_done = True

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

                # Calculate the final fraction of the simulation step.
                winner_time = (
                    finishing_node_computations
                    / finishing_node.search_rate
                    + transcript_time
                )

                # Remove work that would not have been performed
                # because the winning node finished before the
                # other nodes completed their current batch.
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

                # Advance the simulation time by the final
                # fraction of the search interval.
                Node.simulation_time += (
                    winner_time
                )

                # Get the best TSP node found during the search.
                winning_node = (
                    self.node_list[0]
                    .tsp
                    .best_node
                )

                # Calculate the total number of TSP computations.
                total_computations = sum(
                    node.computations
                    for node in self.node_list
                )

                # Add proof-based validation if enabled.
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

                    # Add the validation work to the total.
                    total_computations += (
                        validation_computations
                    )

                    # Add the validation time to the simulation time.
                    Node.simulation_time += (
                        validation_time
                    )

                # Add council validation if enabled.
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

                    # Add the validation work to the total.
                    total_computations += (
                        validation_computations
                    )

                    # Add the validation time to the simulation time.
                    Node.simulation_time += (
                        validation_time
                    )

                # Return the final PoUW simulation results.
                return {
                    "total_computations":
                        total_computations,

                    "simulation_time":
                        Node.simulation_time,

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

            # The search has not finished, so one full second
            # plus the transcript generation time has elapsed.
            round_transcript_time = max(
                result[1]
                for result in results
            )

            Node.simulation_time += (
                1 + round_transcript_time
            )

    # Run all configured simulations and calculate their averages.
    def run_simulation(self):

        # Store the results of every PoW simulation run.
        pow_results = []

        # Run the PoW simulation the configured number of times.
        for _ in range(self.runs):

            # Reset the simulation before starting a new run.
            self.reset_simulation()

            # Run PoW using the configured mining difficulty.
            result = self.multiple_node_pow(
                self.block_hash_difficulty
            )

            # Store the result of this run.
            pow_results.append(result)

        # Store the results of every unvalidated PoUW run.
        pouw_results = []

        # Save the validation mode selected by the user.
        selected_validation_mode = self.validation_mode

        # Temporarily disable validation so the baseline PoUW
        # results measure only the cost of finding the solution.
        self.validation_mode = NO_VALIDATION

        # Run the unvalidated PoUW simulation the configured
        # number of times.
        for _ in range(self.runs):

            # Reset the simulation before starting a new run.
            self.reset_simulation()

            # Run the PoUW TSP simulation without validation.
            result = self.multiple_node_pouw_tsp()

            # Store the result of this run.
            pouw_results.append(result)

        # Store the results of validated PoUW runs.
        validated_pouw_results = []

        # Only run validation when a validation method was selected.
        if selected_validation_mode != NO_VALIDATION:

            # Restore the selected validation mode.
            self.validation_mode = selected_validation_mode

            # Run the validated PoUW simulation the configured
            # number of times.
            for _ in range(self.runs):

                # Reset the simulation before starting a new run.
                self.reset_simulation()

                # Run PoUW with the selected validation method.
                result = self.multiple_node_pouw_tsp()

                # Store the result of this run.
                validated_pouw_results.append(result)

        # Restore the original validation mode.
        self.validation_mode = selected_validation_mode

        # Calculate the average number of hashes across
        # all PoW simulation runs.
        average_hashes = (
            sum(
                result["total_hashes"]
                for result in pow_results
            )
            / len(pow_results)
        )

        # Calculate the average number of computations across
        # all unvalidated PoUW simulation runs.
        average_computations = (
            sum(
                result["total_computations"]
                for result in pouw_results
            )
            / len(pouw_results)
        )

        # Calculate the average PoW simulation time.
        average_pow_simulation_time = (
            sum(
                result["simulation_time"]
                for result in pow_results
            )
            / len(pow_results)
        )

        # Calculate the average unvalidated PoUW simulation time.
        average_pouw_simulation_time = (
            sum(
                result["simulation_time"]
                for result in pouw_results
            )
            / len(pouw_results)
        )

        # Calculate the average hash rate of each PoW node.
        average_pow_hash_rate = {}

        for node_name in pow_results[0]["nodes"]:

            average_pow_hash_rate[node_name] = (
                sum(
                    run["nodes"][node_name]["hash_rate"]
                    for run in pow_results
                )
                / len(pow_results)
            )

        # Calculate the average hash rate of each PoUW node.
        average_pouw_hash_rate = {}

        for node_name in pouw_results[0]["nodes"]:

            average_pouw_hash_rate[node_name] = (
                sum(
                    run["nodes"][node_name]["hash_rate"]
                    for run in pouw_results
                )
                / len(pouw_results)
            )

        # Calculate the average TSP search rate of each PoUW node.
        average_pouw_search_rate = {}

        for node_name in pouw_results[0]["nodes"]:

            average_pouw_search_rate[node_name] = (
                sum(
                    run["nodes"][node_name]["search_rate"]
                    for run in pouw_results
                )
                / len(pouw_results)
            )

        # Calculate the average number of hashes performed
        # by each PoW node.
        average_pow_mining_count = {}

        for node_name in pow_results[0]["nodes"]:

            average_pow_mining_count[node_name] = (
                sum(
                    run["nodes"][node_name]["hashes"]
                    for run in pow_results
                )
                / len(pow_results)
            )

        # Calculate the average number of TSP computations
        # performed by each PoUW node.
        average_pouw_computations = {}

        for node_name in pouw_results[0]["nodes"]:

            average_pouw_computations[node_name] = (
                sum(
                    run["nodes"][node_name]["computations"]
                    for run in pouw_results
                )
                / len(pouw_results)
            )

        # Calculate averages for validated PoUW runs when available.
        if validated_pouw_results:

            # Calculate the average computational work,
            # including the selected validation method.
            average_validated_pouw_computations = (
                sum(
                    result["total_computations"]
                    for result in validated_pouw_results
                )
                / len(validated_pouw_results)
            )

            # Calculate the average simulation time,
            # including the selected validation method.
            average_validated_pouw_simulation_time = (
                sum(
                    result["simulation_time"]
                    for result in validated_pouw_results
                )
                / len(validated_pouw_results)
            )

        else:
            # No validated runs were performed.
            average_validated_pouw_computations = None
            average_validated_pouw_simulation_time = None

        # Return all calculated averages and individual run results.
        return {
            "average_hashes": average_hashes,
            "average_computations": average_computations,
            "average_pow_simulation_time":
                average_pow_simulation_time,
            "average_pouw_simulation_time":
                average_pouw_simulation_time,

            # PoW results.
            "pow": {
                "average_hash_rate":
                    average_pow_hash_rate,

                "average_mining_count":
                    average_pow_mining_count,

                "runs":
                    pow_results
            },

            # PoUW results.
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

            # Validated PoUW results.
            "validated_pouw": {
                "average_computations":
                    average_validated_pouw_computations,

                "average_simulation_time":
                    average_validated_pouw_simulation_time,

                "runs":
                    validated_pouw_results
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

        # Recreate the nodes and generate a new TSP problem.
        # Benchmarks are not run again here.
        self.create_nodes()