from mainFunctions import MainFunctions
import benchmark
import utils

hashes_per_second = utils.average_runs(benchmark.benchmark_pow, 5)
print("PoW Benchmark: ")
print(f"Hashes/sec: {hashes_per_second:.0f}\n")

computations_per_second = utils.average_runs(benchmark.benchmark_tsp_pouw, 5)
print("PoUW TSP Benchmark: ")
print(f"Computations/sec: {computations_per_second:.0f}\n")

block_hash_difficulty = 4
num_of_nodes = 5
num_of_cities = 10
nodes = MainFunctions(num_of_nodes, num_of_cities)

nodes.multiple_node_pow(block_hash_difficulty)
nodes.multiple_node_pouw_tsp()






