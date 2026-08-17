from nodes import Node

class MainFunctions:

    def __init__(self, num_of_nodes, num_of_cities):

        Node.initialize_tsp(num_of_cities)

        self.node_list = []

        for i in range(num_of_nodes):
            node = Node(f"node{i + 1}")
            self.node_list.append(node)

    def multiple_node_pow(self, block_hash_difficulty):

        print("Pow simulation: \n")

        print("Hash rate: ")
        for node in self.node_list:
            print(f"{node.name}: {node.hash_rate}", end="\t")
        print("\n")

        Node.found = False
        Node.simulation_time = 0

        while not Node.found:
            results = [node.pow_mining(block_hash_difficulty) for node in self.node_list]

            successful_nodes = [result for result in results if result is not None]

            if successful_nodes:

                winner = successful_nodes[0]

                print("Winner is: ")
                #print("Node:", winner["node"])
                print("Name: ", winner["name"])
                print("Hashes:", winner["hashes"])
                print(f"Time: {round(winner["time"], 2)}s")
                print("Hash:", winner["hash"])

                Node.found = True

                print("\nMining count: ")
                for node in self.node_list:
                    print(f"{node.name}: {node.mining_count}", end="\t")

                total_mining_count = 0
                for node in self.node_list:
                    total_mining_count += node.mining_count
                print("\n\nTotal mining count:", total_mining_count)
                print("Simulation time:", Node.simulation_time, "s")
                print("\n\n")

                break

            Node.simulation_time += 1

    def multiple_node_pouw_tsp(self):

        print("PoUW TSP simulation: \n")

        print("Matrix: ")
        for row in Node.tsp.matrix:
            print(row)

        print("\nSearch rate: ")
        for node in self.node_list:
            print(f"{node.name}: {node.search_rate}", end="\t")

        Node.tsp.found = False
        Node.tsp.simulation_time = 0

        while not Node.tsp.found:

            for node in self.node_list:
                node.pouw_mining()

            Node.tsp.simulation_time += 1



        print("\nBest path:", self.node_list[0].tsp.best_path)
        print("Best cost:", self.node_list[0].tsp.best_cost)

        print("\nComputations:")
        for node in self.node_list:
            print(f"{node.name}: {node.computations}", end="\t")

        total_computations = 0
        for node in self.node_list:
            total_computations += node.computations
        print("\n\nTotal computations:", total_computations)
        print(f"Simulation time: {Node.simulation_time}s")
