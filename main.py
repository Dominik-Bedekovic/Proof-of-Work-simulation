from mainFunctions import MainFunctions

# Validation modes
NO_VALIDATION = 0
PROOF_VALIDATION = 1
COUNCIL_VALIDATION = 2

# Number of benchmark and simulation repetitions used
# to calculate average results.
runs = 5

# Number of leading zeros required in a valid PoW hash.
block_hash_difficulty = 4

# Number of nodes participating in each simulation.
num_of_nodes = 5

# Number of cities used for the TSP instance in the PoUW simulation.
num_of_cities = 11


def main():

    validation_mode = 0
    validation_mode |= COUNCIL_VALIDATION

    print(f"Validation mode: {validation_mode}")
    print(f"Binary: {validation_mode:02b}")

    if validation_mode & PROOF_VALIDATION:
        print("Proof validation: ENABLED")
    else:
        print("Proof validation: DISABLED")

    if validation_mode & COUNCIL_VALIDATION:
        print("Council validation: ENABLED")
    else:
        print("Council validation: DISABLED")

    # Creates the main simulation object using the defined parameters.
    simulation = MainFunctions(
        num_of_nodes,
        num_of_cities,
        runs,
        block_hash_difficulty,
        validation_mode
    )

    # Starts the PoW and PoUW simulations and calculates their
    # average results over the specified number of runs.
    simulation.run_simulation()


if __name__ == "__main__":
    main()