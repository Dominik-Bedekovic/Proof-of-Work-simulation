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

        MainFunctions.hashes_per_second = (
            utils.average_runs(
                benchmark.benchmark_pow,
                self.runs
            )
        )

        MainFunctions.computations_per_second = (
            utils.average_runs(
                lambda: benchmark.benchmark_tsp_pouw(
                    size=self.num_of_cities
                ),
                self.runs
            )
        )

        # ---------------------------------------------
        # PoUW / PoW ratio
        # ---------------------------------------------

        Node.pouw_pow_ratio = (
            MainFunctions.computations_per_second
            / MainFunctions.hashes_per_second
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

            MainFunctions.benchmarks_done = True

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
        # Create a multiprocessing pool with one worker
        # process for each simulated node.
        with multiprocessing.Pool(
            processes=len(self.node_list)
        ) as pool:

            # Continue the simulation until one node
            # finds a valid proof of work.
            while not Node.found:

                # Prepare the current mining state of
                # every node for the worker processes.
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

                # Run one mining interval for every node
                # in parallel.
                results = pool.map(
                    powWorker.pow_worker,
                    arguments
                )

                # Update the state of nodes that did not
                # find a valid hash during this interval.
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

                # Identify all nodes that found a valid
                # proof of work during this interval.
                successful_nodes = [
                    (index, result)
                    for index, result in enumerate(results)
                    if result["found"]
                ]

                # If no node found a valid hash, assume
                # one second of mining has elapsed.
                if not successful_nodes:

                    for node in self.node_list:
                        node.mining_count += node.hash_rate

                    Node.simulation_time += 1

                    continue

                # Select the first successful node as
                # the winner of the mining round.
                winner_index, winner = successful_nodes[0]

                finishing_node = (
                    self.node_list[winner_index]
                )

                # Number of hashes required by the winner
                # during the final mining interval.
                hashes = winner["hashes"]

                # Calculate the fraction of the final second
                # required for the winning node to find a
                # valid hash.
                winner_time = (
                    hashes
                    / finishing_node.hash_rate
                )

                # Calculate the amount of work performed by
                # every node during the final fraction of
                # the simulated second.
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

                # Advance the simulation clock by the
                # fraction of a second required to find
                # the winning hash.
                Node.simulation_time += winner_time

                # Mark the simulation as finished.
                Node.found = True

                # Calculate the total number of hashes
                # performed by all nodes.
                total_mining_count = sum(
                    node.mining_count
                    for node in self.node_list
                )

                # Return the simulation results to the
                # benchmark and GUI layers.
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

    # =====================================================
    # PROOF OF USEFUL WORK
    # =====================================================

    def multiple_node_pouw_tsp(self):

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

                winning_node = (
                    self.node_list[0]
                    .tsp
                    .best_node
                )

                total_computations = sum(
                    node.computations
                    for node in self.node_list
                )

                # =========================================
                # Calculate total computations
                # =========================================

                total_computations = sum(
                    node.computations
                    for node in self.node_list
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

                    total_computations += (
                        validation_computations
                    )

                    Node.simulation_time += (
                        validation_time
                    )

                # -----------------------------------------
                # Final output.
                # -----------------------------------------

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

        # =========================================================
        # Run PoW simulation
        # =========================================================

        # Stores the results of every PoW simulation run.
        pow_results = []

        # Repeat the PoW simulation the configured number of times.
        for _ in range(self.runs):

            # Reset the blockchain, nodes and simulation state
            # before starting a new independent run.
            self.reset_simulation()

            # Run the PoW simulation using the configured
            # mining difficulty.
            result = self.multiple_node_pow(
                self.block_hash_difficulty
            )

            # Store the result of this run.
            pow_results.append(result)


        # =========================================================
        # Run PoUW simulation without validation
        # =========================================================

        # Stores the results of every unvalidated PoUW run.
        pouw_results = []

        # Save the validation mode selected by the user.
        # It will be restored after the unvalidated runs.
        selected_validation_mode = self.validation_mode

        # Temporarily disable validation so that these runs
        # measure only the computational cost of PoUW mining.
        self.validation_mode = NO_VALIDATION

        # Repeat the PoUW simulation the configured number of times.
        for _ in range(self.runs):

            # Reset the simulation before each independent run.
            self.reset_simulation()

            # Run the PoUW TSP simulation without validation.
            result = self.multiple_node_pouw_tsp()

            # Store the result of this run.
            pouw_results.append(result)


        # =========================================================
        # Run PoUW simulation with validation
        # =========================================================

        # Stores the results of validated PoUW runs.
        validated_pouw_results = []

        # Only perform validated runs when a validation method
        # has actually been selected.
        if selected_validation_mode != NO_VALIDATION:

            # Restore the validation mode selected by the user.
            self.validation_mode = selected_validation_mode

            # Repeat the validated PoUW simulation.
            for _ in range(self.runs):

                # Reset the simulation before each independent run.
                self.reset_simulation()

                # Run PoUW with the selected validation mechanism.
                result = self.multiple_node_pouw_tsp()

                # Store the result of this run.
                validated_pouw_results.append(result)

        # Restore the originally selected validation mode.
        self.validation_mode = selected_validation_mode


        # =========================================================
        # Calculate baseline averages
        # =========================================================

        # Calculate the average number of hashes performed
        # across all PoW simulation runs.
        average_hashes = (
            sum(
                result["total_hashes"]
                for result in pow_results
            )
            / len(pow_results)
        )

        # Calculate the average number of computations performed
        # across all unvalidated PoUW simulation runs.
        average_computations = (
            sum(
                result["total_computations"]
                for result in pouw_results
            )
            / len(pouw_results)
        )


        # =========================================================
        # Calculate average simulation times
        # =========================================================

        # Calculate the average time required by the PoW simulation.
        average_pow_simulation_time = (
            sum(
                result["simulation_time"]
                for result in pow_results
            )
            / len(pow_results)
        )

        # Calculate the average time required by the unvalidated
        # PoUW simulation.
        average_pouw_simulation_time = (
            sum(
                result["simulation_time"]
                for result in pouw_results
            )
            / len(pouw_results)
        )


        # =========================================================
        # Calculate average PoW node hash rates
        # =========================================================

        # Dictionary containing the average hash rate of each
        # individual node across all PoW simulation runs.
        average_pow_hash_rate = {}

        # Iterate through every node that participated in the
        # first PoW simulation run.
        for node_name in pow_results[0]["nodes"]:

            # Calculate the mean hash rate of this node
            # across all PoW runs.
            average_pow_hash_rate[node_name] = (
                sum(
                    run["nodes"][node_name]["hash_rate"]
                    for run in pow_results
                )
                / len(pow_results)
            )


        # =========================================================
        # Calculate average PoUW node hash rates
        # =========================================================

        # Dictionary containing the average hash rate of each
        # individual node across all PoUW simulation runs.
        average_pouw_hash_rate = {}

        for node_name in pouw_results[0]["nodes"]:

            # Calculate the mean hash rate of this node
            # across all PoUW runs.
            average_pouw_hash_rate[node_name] = (
                sum(
                    run["nodes"][node_name]["hash_rate"]
                    for run in pouw_results
                )
                / len(pouw_results)
            )


        # =========================================================
        # Calculate average PoUW search rates
        # =========================================================

        # Dictionary containing the average TSP search rate
        # of each node across all PoUW simulation runs.
        average_pouw_search_rate = {}

        for node_name in pouw_results[0]["nodes"]:

            # Calculate the mean search rate of this node
            # across all PoUW runs.
            average_pouw_search_rate[node_name] = (
                sum(
                    run["nodes"][node_name]["search_rate"]
                    for run in pouw_results
                )
                / len(pouw_results)
            )


        # =========================================================
        # Calculate average PoW mining counts
        # =========================================================

        # Dictionary containing the average number of hashes
        # performed by each PoW node before the solution was found.
        average_pow_mining_count = {}

        for node_name in pow_results[0]["nodes"]:

            # Calculate the mean number of hashes performed by
            # this node across all PoW runs.
            average_pow_mining_count[node_name] = (
                sum(
                    run["nodes"][node_name]["hashes"]
                    for run in pow_results
                )
                / len(pow_results)
            )


        # =========================================================
        # Calculate average PoUW computations
        # =========================================================

        # Dictionary containing the average number of TSP
        # computations performed by each node.
        average_pouw_computations = {}

        for node_name in pouw_results[0]["nodes"]:

            # Calculate the mean number of computations performed
            # by this node across all PoUW runs.
            average_pouw_computations[node_name] = (
                sum(
                    run["nodes"][node_name]["computations"]
                    for run in pouw_results
                )
                / len(pouw_results)
            )


        # =========================================================
        # Calculate average validated PoUW results
        # =========================================================

        # Check whether any validated PoUW runs were performed.
        if validated_pouw_results:

            # Calculate the average total computational work
            # including the selected validation mechanism.
            average_validated_pouw_computations = (
                sum(
                    result["total_computations"]
                    for result in validated_pouw_results
                )
                / len(validated_pouw_results)
            )

            # Calculate the average simulation time including
            # the additional validation process.
            average_validated_pouw_simulation_time = (
                sum(
                    result["simulation_time"]
                    for result in validated_pouw_results
                )
                / len(validated_pouw_results)
            )

        else:

            # No validated runs were performed, so no averages
            # can be calculated.
            average_validated_pouw_computations = None
            average_validated_pouw_simulation_time = None


        # =========================================================
        # Return all simulation results
        # =========================================================

        # Return a dictionary containing the calculated averages
        # as well as the complete results of every individual run.
        return {

            # Average number of hashes across all PoW runs.
            "average_hashes": average_hashes,

            # Average number of computations across all
            # unvalidated PoUW runs.
            "average_computations": average_computations,

            # Average PoW simulation time.
            "average_pow_simulation_time":
                average_pow_simulation_time,

            # Average unvalidated PoUW simulation time.
            "average_pouw_simulation_time":
                average_pouw_simulation_time,


            # =====================================================
            # PoW results
            # =====================================================

            "pow": {

                # Average hash rate for each PoW node.
                "average_hash_rate":
                    average_pow_hash_rate,

                # Average number of hashes performed by
                # each PoW node.
                "average_mining_count":
                    average_pow_mining_count,

                # Results from every individual PoW run.
                "runs":
                    pow_results
            },


            # =====================================================
            # PoUW results
            # =====================================================

            "pouw": {

                # Average hash rate for each PoUW node.
                "average_hash_rate":
                    average_pouw_hash_rate,

                # Average TSP search rate for each PoUW node.
                "average_search_rate":
                    average_pouw_search_rate,

                # Average number of TSP computations for
                # each PoUW node.
                "average_computations":
                    average_pouw_computations,

                # Results from every individual PoUW run.
                "runs":
                    pouw_results
            },


            # =====================================================
            # Validated PoUW results
            # =====================================================

            "validated_pouw": {

                # Average computational work including validation.
                "average_computations":
                    average_validated_pouw_computations,

                # Average simulation time including validation.
                "average_simulation_time":
                    average_validated_pouw_simulation_time,

                # Results from every individual validated run.
                "runs":
                    validated_pouw_results
            }
        }


    # =============================================================
    # Reset simulation
    # =============================================================

    def reset_simulation(self):

        # ---------------------------------------------------------
        # Generate a new block
        # ---------------------------------------------------------

        # Create a new block containing fresh block data,
        # such as transactions, timestamp and previous hash.
        Node.blockData = BlockData()


        # ---------------------------------------------------------
        # Reset simulation state
        # ---------------------------------------------------------

        # Mark the simulation as unfinished so that the mining
        # process can start again.
        Node.found = False

        # Reset the accumulated simulation time to zero.
        Node.simulation_time = 0


        # ---------------------------------------------------------
        # Recreate nodes and TSP problem
        # ---------------------------------------------------------

        # Recreate all nodes and generate a new TSP instance
        # using the current simulation configuration.
        #
        # This function only recreates the simulation state;
        # benchmark measurements are not performed here.
        self.create_nodes()