import time

from nodes import Node
from blockFunctions import BlockFunctions
from tspData import TspData
from tspFunctions import TspFunction


# Measures the SHA-256 hashing rate used as the computational
# workload for the PoW simulation.
def benchmark_pow(num_hashes=100000):

    # Create a node whose block data and mining data are used
    # as input for the benchmark.
    benchmark_node = Node("benchmark")

    # Start measuring the execution time of the benchmark.
    start = time.perf_counter()

    # Generate the specified number of block header hashes.
    # Each hash represents one simulated PoW mining attempt.
    for _ in range(num_hashes):
        BlockFunctions.create_header_hash(
            benchmark_node.blockData.previous_hash,
            benchmark_node.blockData.timestamp,
            benchmark_node.merkle_root,
            benchmark_node.nonce
        )

        # Increment the nonce so that each iteration produces a different block header hash.
        benchmark_node.nonce += 1

    # Calculate the total time required to perform the hashing.
    elapsed = time.perf_counter() - start

    # Return the measured hashing rate in hashes per second.
    return num_hashes / elapsed


# Measures the processing rate of the TSP Branch and Bound
def benchmark_tsp_pouw(num_of_computations=10000):

    # Generate a TSP problem containing 10 cities.
    benchmark_tsp = TspData(size=10)

    # Start measuring the execution time of the benchmark.
    start = time.perf_counter()

    # Execute the TSP solver for the specified number of
    # computational operations and record the number performed.
    computations, _ = TspFunction.tsp_solver(
        benchmark_tsp,
        num_of_computations
    )

    # Calculate the total time required to perform the TSP computations.
    elapsed = time.perf_counter() - start

    # Return the measured TSP processing rate in operations per second.
    return computations / elapsed