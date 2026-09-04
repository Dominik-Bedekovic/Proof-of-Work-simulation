import hashlib
import random
import string


# Represents an infinite value
inf = float("inf")


def random_string(char_num):
    # Generates a random alphanumeric string of the requested length.
    # Used for generating simulated block data and transactions.
    return ''.join(
        random.choices(
            string.ascii_letters + string.digits,
            k=char_num
        )
    )


def create_hash(data):
    # Calculates the SHA-256 hash of the provided data.
    # Used for generating hashes during the PoW simulation.
    if isinstance(data, str):
        data = data.encode()
    
    return hashlib.sha256(data).hexdigest()

def random_num(min_num, max_num):
    # Generates a random integer within the specified range.
    # Used throughout the simulation for generating random
    # parameters and input data.
    random_num = random.randint(
        min_num,
        max_num
    )

    return random_num


def random_transactions():
    # Generates a random number of simulated transactions
    # and stores them as a tuple.
    transactions = list()

    # The number of transactions is randomly selected between 5 and 20.
    num_of_elements = random_num(5, 20)

    while num_of_elements > 0:
        num_of_elements -= 1

        # Each transaction is represented by a random
        # alphanumeric string of 10 characters.
        transactions.append(
            random_string(10)
        )

    return tuple(transactions)

# Executes the provided function multiple times and calculates
# the arithmetic mean of the obtained results.
# Used to reduce the influence of individual measurement variations
# during benchmarking and simulation.
def average_runs(function, runs):

    results = []

    for _ in range(runs):
        results.append(function())

    if isinstance(results[0], dict):
        return results

    return sum(results) / len(results)