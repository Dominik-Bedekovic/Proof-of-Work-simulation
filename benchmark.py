import time
from nodes import Node
from blockFunctions import BlockFunctions
from tspData import TspData
from tspFunctions import TspFunction

def benchmark_pow(num_hashes=100000):

    benchmark_node = Node("benchmark")

    start = time.perf_counter()

    for _ in range(num_hashes):
        BlockFunctions.create_header_hash(
            benchmark_node.blockData.previous_hash,
            benchmark_node.blockData.timestamp,
            benchmark_node.merkle_root,
            benchmark_node.nonce
        )

        benchmark_node.nonce += 1
        

    elapsed = time.perf_counter() - start

    return num_hashes / elapsed

def benchmark_tsp_pouw(num_of_computations=10000):

    benchmark_tsp = TspData(size=10)

    start = time.perf_counter()

    computations = TspFunction.tsp_solver(benchmark_tsp, num_of_computations)

    elapsed = time.perf_counter() - start

    return computations / elapsed