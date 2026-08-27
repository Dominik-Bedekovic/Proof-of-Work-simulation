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
def benchmark_tsp_pouw(duration=1.0, size=11):

    print("\n--- PoUW TSP benchmark ---")
    print(f"Benchmark duration: {duration:.2f}s")
    print(f"TSP size: {size} cities")

    

    computations = 0

    # Start measuring only the actual B&B search.
    start = time.perf_counter()

    while (time.perf_counter() - start < duration):

        # Create a TSP instance.
        benchmark_tsp = TspData(size=size)

        computations, _ = TspFunction.tsp_solver(benchmark_tsp, 1000000)

    elapsed = time.perf_counter() - start
    computation_rate = computations / elapsed

    print(f"Elapsed time: {elapsed:.4f}s")
    print(f"Computations performed: {computations}")
    print(
        f"Computation rate: "
        f"{computation_rate:.2f} computations/s"
    )

    return computation_rate