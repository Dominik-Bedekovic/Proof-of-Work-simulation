from nodes import Node
import powWorker
import tspWorker
from tspNode import TspNode
import utils
import benchmark
import multiprocessing
import time
from blockData import BlockData
from tspFunctions import TspFunction
from validation import council_validation
from validation import proof_based_validation


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

                # -------------------------------------------------
                # Update every node with the work performed by its
                # worker during this simulation second.
                # -------------------------------------------------

                for node, result in zip(
                    self.node_list,
                    results
                ):

                    if not result["found"]:

                        node.nonce = result["nonce"]

                        node.coinbase["extra_nonce"] = (
                            result["extra_nonce"]
                        )

                        node.merkle_root = result["merkle_root"]

                # -------------------------------------------------
                # Check whether one or more workers found a hash.
                # -------------------------------------------------

                successful_nodes = [
                    (index, result)
                    for index, result in enumerate(results)
                    if result["found"]
                ]

                if not successful_nodes:

                    for node in self.node_list:
                        node.mining_count += node.hash_rate

                    Node.simulation_time += 1

                    continue

                # Nobody found a valid hash.
                if not successful_nodes:

                    Node.simulation_time += 1
                    continue

                # -------------------------------------------------
                # A worker found a valid hash.
                # -------------------------------------------------

                winner_index, winner = successful_nodes[0]

                finishing_node = self.node_list[winner_index]

                hashes = winner["hashes"]

                # -------------------------------------------------
                # Calculate how much of this second elapsed.
                # -------------------------------------------------

                winner_time = (
                    hashes / finishing_node.hash_rate
                )

                # -------------------------------------------------
                # Calculate how many hashes every node actually
                # performed before the winner stopped the simulation.
                # -------------------------------------------------

                for node in self.node_list:

                    work_done = round(
                        node.hash_rate * winner_time
                    )

                    node.mining_count += work_done

                # -------------------------------------------------
                # Save the winning state.
                # -------------------------------------------------

                finishing_node.nonce = winner["nonce"]

                finishing_node.coinbase["extra_nonce"] = (
                    winner["extra_nonce"]
                )

                finishing_node.merkle_root = (
                    winner["merkle_root"]
                )

                finishing_node.header_hash = (
                    winner["header_hash"]
                )

                # -------------------------------------------------
                # Update simulation time.
                # -------------------------------------------------

                Node.simulation_time += winner_time

                Node.found = True

                # -------------------------------------------------
                # Output.
                # -------------------------------------------------

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

    def multiple_node_pouw(self):

        print("\nParallel TSP solver:\n")

        matrix = Node.tsp.matrix
        size = Node.tsp.size

        manager = multiprocessing.Manager()

        # -------------------------------------------------
        # Shared state
        # -------------------------------------------------

        best_cost = manager.Value(
            'd',
            float('inf')
        )

        best_path = manager.list()

        best_lock = manager.Lock()

        branch_queue = manager.list()

        queue_lock = manager.Lock()

        active_workers = manager.Value(
            'i',
            0
        )

        finished = manager.Event()

        result_queue = manager.Queue()

        # -------------------------------------------------
        # STEP 1:
        # Get an initial solution using greedy search.
        #
        # This is our UPPER BOUND.
        # -------------------------------------------------

        greedy_cost, greedy_path = TspFunction.greedy_tsp(
            matrix
        )

        best_cost.value = greedy_cost
        best_path[:] = greedy_path

        print(
            f"Greedy solution: {greedy_path}"
        )

        print(
            f"Initial upper bound: {greedy_cost}"
        )

        # -------------------------------------------------
        # STEP 2:
        # Create the root node.
        # -------------------------------------------------

        root = TspNode(size)

        root.matrix = [
            row[:]
            for row in Node.tsp.reduced_matrix
        ]

        root.path = [0]
        root.vertex = 0
        root.visited = 0
        root.cost = Node.tsp.cost
        root.total_cost = 0

        # -------------------------------------------------
        # STEP 3:
        # Generate the initial branches.
        #
        # All workers will use the SAME shared queue.
        # -------------------------------------------------

        for city in range(1, size):

            branch = TspFunction._create_child(
                root,
                matrix,
                0,
                city
            )

            if branch.cost >= best_cost.value:

                print(
                    f"Initial branch {branch.path} "
                    f"PRUNED "
                    f"LB={branch.cost} "
                    f">= UB={best_cost.value}"
                )

                continue

            branch_queue.append(branch)

            print(
                f"Initial branch {branch.path} "
                f"LB={branch.cost}"
            )

        # -------------------------------------------------
        # STEP 4:
        # Start exactly one worker per node.
        #
        # Every worker takes branches from the SAME queue.
        # -------------------------------------------------

        processes = []

        worker_count = len(self.node_list)

        for node_index in range(worker_count):

            process = multiprocessing.Process(
                target=tspWorker.tsp_worker,
                args=(
                    node_index,
                    matrix,
                    size,
                    branch_queue,
                    queue_lock,
                    best_cost,
                    best_path,
                    best_lock,
                    active_workers,
                    finished,
                    result_queue
                )
            )

            processes.append(process)

        # -------------------------------------------------
        # STEP 5:
        # Start workers.
        # -------------------------------------------------

        start_time = time.perf_counter()

        for process in processes:
            process.start()

        # -------------------------------------------------
        # STEP 6:
        # Wait for workers.
        # -------------------------------------------------

        for process in processes:
            process.join()

        simulation_time = (
            time.perf_counter()
            - start_time
        )

        # -------------------------------------------------
        # STEP 7:
        # Collect computation counts.
        # -------------------------------------------------

        computations = []

        while not result_queue.empty():

            computations.append(
                result_queue.get()
            )

        computations.sort()

        total_computations = 0

        print("\nParallel TSP result:")

        print(
            "Best path:",
            list(best_path)
        )

        print(
            "Best cost:",
            best_cost.value
        )

        print("\nComputations:")

        for node_index, count in computations:

            print(
                f"node{node_index + 1}: {count}",
                end="\t"
            )

            total_computations += count

        print(
            "\nTotal computations:",
            total_computations
        )

        print(
            f"Simulation time: "
            f"{simulation_time:.2f}s"
        )

        manager.shutdown()

        return total_computations

    def run_simulation(self):

        # Define one complete PoW simulation run.
        def run_pow():
            self.reset_simulation()
            return self.multiple_node_pow(self.block_hash_difficulty)

        # Define one complete PoUW simulation run.
        def run_pouw():
            self.reset_simulation()
            return self.multiple_node_pouw()

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