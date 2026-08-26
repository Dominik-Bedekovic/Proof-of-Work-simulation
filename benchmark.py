import time
import heapq

from nodes import Node
from blockFunctions import BlockFunctions
from tspData import TspData
from tspNode import TspNode
from tspFunctions import TspFunction

import utils


# Measures the SHA-256 hashing rate used as the
# computational workload for the PoW simulation.
def benchmark_pow(duration=1.0):

    print("\n--- PoW benchmark ---")
    print(f"Benchmark duration: {duration:.2f}s")

    benchmark_node = Node("benchmark")

    hashes = 0

    start = time.perf_counter()

    while time.perf_counter() - start < duration:

        BlockFunctions.create_header_hash(
            benchmark_node.blockData.previous_hash,
            benchmark_node.blockData.timestamp,
            benchmark_node.merkle_root,
            benchmark_node.nonce
        )

        benchmark_node.nonce += 1
        hashes += 1

    elapsed = time.perf_counter() - start
    hash_rate = hashes / elapsed

    print(f"Elapsed time: {elapsed:.4f}s")
    print(f"Hashes performed: {hashes}")
    print(f"Hash rate: {hash_rate:.2f} hashes/s")

    return hash_rate


# Measures the Branch and Bound search-node processing rate
# used as the computational workload for the PoUW simulation.
def benchmark_tsp_pouw(duration=1.0, size=0):

    print("\n--- PoUW TSP benchmark ---")
    print(f"Benchmark duration: {duration:.2f}s")
    print(f"TSP size: {size} cities")

    # Create a TSP instance.
    benchmark_tsp = TspData(size=size)

    # Obtain an initial feasible solution.
    # This provides the upper bound.
    best_cost, best_path = TspFunction.greedy_tsp(
        benchmark_tsp.matrix
    )

    print(f"Initial greedy cost: {best_cost}")
    print(f"Initial greedy path: {best_path}")

    # Create the root node.
    root = TspNode(benchmark_tsp.size)

    root.matrix = [
        row[:]
        for row in benchmark_tsp.reduced_matrix
    ]

    root.path = [0]
    root.vertex = 0
    root.visited = 0
    root.cost = benchmark_tsp.cost
    root.total_cost = 0

    # Create the initial branches.
    priority_queue = []

    for city in range(1, benchmark_tsp.size):

        child = TspFunction._create_child(
            root,
            benchmark_tsp.matrix,
            0,
            city
        )

        if child.cost < best_cost:
            heapq.heappush(
                priority_queue,
                child
            )

    print(
        f"Initial branches in queue: "
        f"{len(priority_queue)}"
    )

    computations = 0

    # Start measuring only the actual B&B search.
    start = time.perf_counter()

    while (
        priority_queue
        and time.perf_counter() - start < duration
    ):

        current_node = heapq.heappop(
            priority_queue
        )

        computations += 1

        # Branch and Bound pruning.
        if current_node.cost >= best_cost:
            continue

        # Check whether all cities have been visited.
        if current_node.visited == benchmark_tsp.size - 1:

            final_edge = benchmark_tsp.matrix[
                current_node.vertex
            ][0]

            if final_edge == utils.inf:
                continue

            total_cost = (
                current_node.total_cost
                + final_edge
            )

            if total_cost < best_cost:
                best_cost = total_cost

            continue

        # Expand the current search node.
        for neighbour in range(current_node.size):

            if current_node.matrix[
                current_node.vertex
            ][neighbour] == utils.inf:
                continue

            if neighbour in current_node.path:
                continue

            child = TspFunction._create_child(
                current_node,
                benchmark_tsp.matrix,
                current_node.vertex,
                neighbour
            )

            if child.cost < best_cost:
                heapq.heappush(
                    priority_queue,
                    child
                )

    elapsed = time.perf_counter() - start
    computation_rate = computations / elapsed

    print(f"Elapsed time: {elapsed:.4f}s")
    print(f"Computations performed: {computations}")
    print(f"Final best cost: {best_cost}")
    print(f"Remaining queue size: {len(priority_queue)}")
    print(
        f"Computation rate: "
        f"{computation_rate:.2f} computations/s"
    )

    return computation_rate