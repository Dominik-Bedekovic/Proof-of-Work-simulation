from nodes import Node

class MainFunctions:

    def __init__(self, num_of_nodes):

        self.node_list = []

        for i in range(num_of_nodes):
            node = Node(f"node{i + 1}")
            self.node_list.append(node)

    def multiple_node_pow(self, difficulty: int):

        for node in self.node_list:
            print(f"{node.name}: {node.hash_rate}", end="\t")

        while not Node.found:
            results = [node.pow_mining(difficulty) for node in self.node_list]

            successful_nodes = [result for result in results if result is not None]

            if successful_nodes:

                winner = successful_nodes[0]

                print("Winner is: ")
                #print("Node:", winner["node"])
                print("Name: ", winner["name"])
                print("Hashes:", winner["hashes"])
                print(f"Time: {winner["time"]}s")
                print(f"Exact Time: {round(winner["exact time"], 2)}s")
                print("Hash:", winner["hash"])

                Node.found = True
                break

            Node.simulation_time += 1