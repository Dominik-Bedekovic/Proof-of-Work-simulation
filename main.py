from mainFunctions import MainFunctions

runs = 5
block_hash_difficulty = 4
num_of_nodes = 5
num_of_cities = 10

simulation = MainFunctions(
    num_of_nodes,
    num_of_cities, 
    runs,
    block_hash_difficulty
    )

simulation.run_simulation()






