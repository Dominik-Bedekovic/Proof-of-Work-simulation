from mainFunctions import MainFunctions

block_hash_difficulty = 4
num_of_nodes = 5
num_of_cities = 10
nodes = MainFunctions(num_of_nodes, num_of_cities)

nodes.multiple_node_pow(block_hash_difficulty)
nodes.multiple_node_pouw_tsp()






