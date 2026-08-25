from nodes import Node
import utils
import benchmark
from blockData import BlockData
from validation import council_validation


class MainFunctions:

    def __init__(
        self,
        num_of_nodes,
        num_of_cities,
        runs,
        block_hash_difficulty
    ):
        # Store the main simulation parameters.
        self.num_of_nodes = num_of_nodes
        self.num_of_cities = num_of_cities
        self.runs = runs
        self.block_hash_difficulty = block_hash_difficulty

        # Measure the average PoW hash rate over multiple benchmark runs.
        hashes_per_second = utils.average_runs(
            benchmark.benchmark_pow,
            runs
        )

        print("PoW Benchmark: ")
        print(f"Hashes/sec: {hashes_per_second:.0f}\n")

        # Measure the average PoUW TSP computation rate.
        computations_per_second = utils.average_runs(
            benchmark.benchmark_tsp_pouw,
            runs
        )

        print("PoUW TSP Benchmark: ")
        print(f"Computations/sec: {computations_per_second:.0f}\n")

        # Calculate the ratio between PoUW computations and PoW hashes.
        # This ratio is used to convert a node's hash rate into its
        # corresponding PoUW search rate.
        Node.pouw_pow_ratio = (
            computations_per_second / hashes_per_second
        )

        # Create the nodes used by both simulations.
        self.create_nodes()


    def create_nodes(self):

        # Generate the shared TSP problem for all PoUW nodes.
        Node.initialize_tsp(self.num_of_cities)

        self.node_list = []

        # Create the requested number of nodes.
        for i in range(self.num_of_nodes):
            node = Node(f"node{i + 1}")
            self.node_list.append(node)


    def multiple_node_pow(self, block_hash_difficulty):

        print("Pow simulation: \n")

        # Display the simulated hash rate of every node.
        print("Hash rate: ")
        for node in self.node_list:
            print(
                f"{node.name}: {node.hash_rate}",
                end="\t"
            )
        print("\n")

        # Continue until one of the nodes finds a valid hash.
        while not Node.found:

            # Each node performs one batch of hash attempts.
            results = [
                node.pow_mining(block_hash_difficulty)
                for node in self.node_list
            ]

            # Identify nodes that found a valid hash during this step.
            successful_nodes = [
                (node, result)
                for node, result in zip(self.node_list, results)
                if result is not None
            ]

            if successful_nodes:

                # The first successful node is considered the winner.
                winner, hashes = successful_nodes[0]

                # Determine the fraction of the final simulation step
                # that elapsed before the winning node found its hash.
                final_hashes = (
                    hashes - Node.simulation_time * winner.hash_rate
                )

                winner_time = (
                    final_hashes / winner.hash_rate
                )

                # Remove the unused portion of the final batch from
                # every node that did not find the winning hash.
                for node in self.node_list:
                    if node is not winner:

                        full_batch = node.hash_rate

                        final_batch = round(
                            node.hash_rate * winner_time
                        )

                        node.mining_count -= (
                            full_batch - final_batch
                        )

                print("Winner is:")
                print("Name:", winner.name)
                print("Hashes:", hashes)
                print(
                    f"Time: "
                    f"{round(hashes / winner.hash_rate, 2)}s"
                )
                print("Hash:", winner.header_hash)

                Node.found = True

                print("\nMining count: ")

                for node in self.node_list:
                    print(
                        f"{node.name}: {node.mining_count}",
                        end="\t"
                    )

                # Calculate the total computational work performed
                # by all nodes before the winning hash was found.
                total_mining_count = sum(
                    node.mining_count
                    for node in self.node_list
                )

                print(
                    "\n\nTotal mining count:",
                    total_mining_count
                )

                # Add the fractional final step to the simulation time.
                Node.simulation_time += winner_time

                print(
                    "Simulation time:",
                    Node.simulation_time,
                    "s"
                )

                print("\n\n")

                return total_mining_count

            # If no node has found a solution, advance the simulation
            # by one complete time step.
            Node.simulation_time += 1


    def multiple_node_pouw_tsp(self):

        print("PoUW TSP simulation: \n")

        # Display the TSP distance matrix shared by all nodes.
        print("Matrix: ")
        for row in Node.tsp.matrix:
            print(row)

        # Display the simulated search rate of every node.
        print("\nSearch rate: ")
        for node in self.node_list:
            print(
                f"{node.name}: {node.search_rate}",
                end="\t"
            )

        # Continue until the TSP search has been completed.
        while not Node.found:

            results = []

            # Each node processes a batch of nodes from the shared
            # Branch and Bound search tree.
            for node in self.node_list:

                computations, finished = node.pouw_mining()

                results.append(
                    (computations, finished)
                )

                # The search is finished when the priority queue
                # has been exhausted.
                if finished:
                    Node.found = True

            if Node.found:

                # Find the node that completed the TSP search.
                winner_index = next(
                    i for i, result in enumerate(results)
                    if result[1]
                )

                winner = self.node_list[winner_index]

                winner_computations = (
                    results[winner_index][0]
                )

                # Calculate the fraction of the final simulation
                # step required by the winning node.
                winner_time = (
                    winner_computations / winner.search_rate
                )

                # Remove the unused portion of the final batch from
                # nodes that did not finish the search.
                for i, node in enumerate(
                    self.node_list[:len(results)]
                ):

                    if node is not winner:

                        computation_done = results[i][0]

                        final_batch = round(
                            node.search_rate
                            * winner_time
                        )

                        node.computations -= (
                            computation_done
                            - final_batch
                        )

                # Add the fractional final step to the simulation time.
                Node.simulation_time += winner_time

                print(
                    "\nBest path:",
                    self.node_list[0].tsp.best_path
                )

                print(
                    "Best cost:",
                    self.node_list[0].tsp.best_cost
                )

                winning_node = self.node_list[0].tsp.best_node

                print("\nWinning TSP node:")
                print("Name:", winner.name)
                print("Path:", winning_node.path)
                print("Cost:", winning_node.cost)
                print("Total cost:", winning_node.total_cost)
                print("Vertex:", winning_node.vertex)
                print("Visited:", winning_node.visited)

                print("\nComputations:")

                for node in self.node_list:
                    print(
                        f"{node.name}: {node.computations}",
                        end="\t"
                    )

                # Calculate the total computational work performed
                # by all nodes.
                total_computations = sum(
                    node.computations
                    for node in self.node_list
                )

                print(
                    "\n\nTotal computations:",
                    total_computations
                )

                print(
                    f"Simulation time: "
                    f"{Node.simulation_time:.2f}s"
                )

                print("\n\n")

                council = [
                    node for node in self.node_list
                    if node is not winner
                ]

                result = council_validation(
                            self.node_list[0].tsp,
                            council,
                            self.node_list[0].tsp.best_path,
                            self.node_list[0].tsp.best_cost
                        )

                print(f"Council result: {result}")

                return total_computations

            # If the search is not finished, advance the simulation
            # by one complete time step.
            Node.simulation_time += 1


    def run_simulation(self):

        # Define one complete PoW simulation run.
        def run_pow():
            self.reset_simulation()
            return self.multiple_node_pow(self.block_hash_difficulty)

        # Define one complete PoUW simulation run.
        def run_pouw():
            self.reset_simulation()
            return self.multiple_node_pouw_tsp()

        # Repeat the PoW simulation and calculate its average
        # computational work.
        average_hashes = utils.average_runs(run_pow, self.runs)

        # Repeat the PoUW simulation and calculate its average
        # computational work.
        average_computations = utils.average_runs(run_pouw, self.runs)

        print(
            f"Average hashes: "
            f"{average_hashes:.2f}"
        )

        print(
            f"Average computation: "
            f"{average_computations:.2f}"
        )

        return average_hashes, average_computations


    def reset_simulation(self):

        # Generate a new block so that each simulation run uses
        # different block data.
        Node.blockData = BlockData()

        # Reset the shared simulation state.
        Node.found = False
        Node.simulation_time = 0

        # Recreate the nodes and the shared TSP problem.
        self.create_nodes()