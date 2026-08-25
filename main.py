from mainFunctions import MainFunctions


# Number of benchmark and simulation repetitions used
# to calculate average results.
runs = 5

# Number of leading zeros required in a valid PoW hash.
block_hash_difficulty = 4

# Number of nodes participating in each simulation.
num_of_nodes = 5

# Number of cities used for the TSP instance in the PoUW simulation.
num_of_cities = 10


# Creates the main simulation object using the defined parameters.
simulation = MainFunctions(
    num_of_nodes,
    num_of_cities,
    runs,
    block_hash_difficulty
)


# Starts the PoW and PoUW simulations and calculates their
# average results over the specified number of runs.
simulation.run_simulation()