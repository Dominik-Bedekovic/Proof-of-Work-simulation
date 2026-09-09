"""Small helpers for random sample data, SHA-256 hashing, and repeated measurements."""

import hashlib
import random
import string

inf = float("inf")


def random_string(char_num):
    """Return an alphanumeric sample string of the requested length."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=char_num))


def create_hash(data):
    """Return a SHA-256 hexadecimal digest; encode text as UTF-8 first."""
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


def random_num(min_num, max_num):
    """Return a uniformly selected integer between the inclusive bounds."""
    random_num = random.randint(min_num, max_num)
    return random_num


def random_transactions():
    """Return a tuple of 5–20 random transaction strings for sample block data."""
    transactions = list()
    num_of_elements = random_num(5, 20)
    while num_of_elements > 0:
        num_of_elements -= 1
        transactions.append(random_string(10))
    return tuple(transactions)


def average_runs(function, runs):
    """Repeat a function; average numeric results or preserve a list of dictionary
    results.
    """
    results = []
    for _ in range(runs):
        results.append(function())

    # Simulation dictionaries are retained; arithmetic averaging applies only to numeric rates.
    if isinstance(results[0], dict):
        return results
    return sum(results) / len(results)
