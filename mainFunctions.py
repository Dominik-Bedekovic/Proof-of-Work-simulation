from nodes import Node
import utils
import benchmark
from blockData import BlockData

class MainFunctions:

    def __init__(self, num_of_nodes, num_of_cities, runs, block_hash_difficulty):

        self.num_of_nodes = num_of_nodes
        self.num_of_cities = num_of_cities
        self.runs = runs
        self.block_hash_difficulty = block_hash_difficulty

        hashes_per_second = utils.average_runs(benchmark.benchmark_pow, runs)
        print("PoW Benchmark: ")
        print(f"Hashes/sec: {hashes_per_second:.0f}\n")
        
        computations_per_second = utils.average_runs(benchmark.benchmark_tsp_pouw, runs)
        print("PoUW TSP Benchmark: ")
        print(f"Computations/sec: {computations_per_second:.0f}\n")

        Node.pouw_pow_ratio = computations_per_second / hashes_per_second

        self.create_nodes()

    def create_nodes(self):

        Node.initialize_tsp(self.num_of_cities)

        self.node_list = []

        for i in range(self.num_of_nodes):
            node = Node(f"node{i + 1}")
            self.node_list.append(node)

    def multiple_node_pow(self, block_hash_difficulty):

        print("Pow simulation: \n")

        print("Hash rate: ")
        for node in self.node_list:
            print(f"{node.name}: {node.hash_rate}", end="\t")
        print("\n")

        while not Node.found:
            results = [node.pow_mining(block_hash_difficulty) for node in self.node_list]

            successful_nodes = [(node, result) for node, result in zip(self.node_list, results)
                                if result is not None]

            if successful_nodes:

                winner, hashes = successful_nodes[0]
                final_hashes = hashes - Node.simulation_time * winner.hash_rate
                winner_time = final_hashes / winner.hash_rate

                for node in self.node_list:
                    if node is not winner:
                        full_batch = node.hash_rate
                        final_batch = round(node.hash_rate * winner_time)
                        node.mining_count -= full_batch - final_batch

                print("Winner is:") 
                print("Name:", winner.name)
                print("Hashes:", hashes)
                print(f"Time: {round(hashes / winner.hash_rate, 2)}s")
                print("Hash:", winner.header_hash)

                Node.found = True

                print("\nMining count: ")
                for node in self.node_list:
                    print(f"{node.name}: {node.mining_count}", end="\t")

                total_mining_count = sum(node.mining_count for node in self.node_list)
                print("\n\nTotal mining count:", total_mining_count)

                Node.simulation_time += winner_time
                print("Simulation time:", Node.simulation_time, "s")
                print("\n\n")


                return total_mining_count

            Node.simulation_time += 1

    def multiple_node_pouw_tsp(self):

        print("PoUW TSP simulation: \n")

        print("Matrix: ")
        for row in Node.tsp.matrix:
            print(row)

        print("\nSearch rate: ")
        for node in self.node_list:
            print(f"{node.name}: {node.search_rate}", end="\t")

        while not Node.found:

            results = []

            for node in self.node_list:
                computations, finished = node.pouw_mining()
                results.append((computations, finished))

                if finished:
                    Node.found = True

            if Node.found:

                winner_index = next(
                    i for i, result in enumerate(results)
                    if result[1]
                )

                winner = self.node_list[winner_index]
                winner_computations = results[winner_index][0]

                winner_time = winner_computations / winner.search_rate

                for i, node in enumerate(self.node_list[:len(results)]):

                    if node is not winner:

                        computation_done = results[i][0]

                        final_batch = round(node.search_rate * winner_time)

                        node.computations -= computation_done - final_batch

                Node.simulation_time += winner_time

                print("\nBest path:", self.node_list[0].tsp.best_path)
                print("Best cost:", self.node_list[0].tsp.best_cost)

                print("\nComputations:")
                for node in self.node_list:
                    print(f"{node.name}: {node.computations}", end="\t")
                
                total_computations = sum (node.computations for node in self.node_list)
                print("\n\nTotal computations:", total_computations)
                print(f"Simulation time: {Node.simulation_time:.2f}s")

                print("\n\n")

                return total_computations

                
            Node.simulation_time += 1

    def run_simulation(self):

        def run_pow():
            self.reset_simulation()
            return self.multiple_node_pow(self.block_hash_difficulty)

        def run_pouw():
            self.reset_simulation()
            return self.multiple_node_pouw_tsp()

        average_hashes = utils.average_runs(run_pow, self.runs)
        average_computations = utils.average_runs(run_pouw, self.runs)

        print(f"Average hashes: {average_hashes:.2f}")
        print(f"Average computation: {average_computations:.2f}")

    def reset_simulation(self):

        Node.blockData = BlockData()

        Node.found = False
        Node.simulation_time = 0

        self.create_nodes()