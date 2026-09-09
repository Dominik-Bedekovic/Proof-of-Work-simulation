"""Represent a partial tour with its reduced matrix and lower bound."""

import utils


class TspNode:
    """One partial route, including its actual distance and a bound on any completion."""

    def __init__(self, size=0):
        """Initialize the route, matrix, vertex, and separate bound/distance fields."""
        self.size = size
        self.matrix = [[utils.inf] * self.size for _ in range(self.size)]
        self.path = []
        self.vertex = 0

        # Counts edges taken from zero; a node with n - 1 edges has visited all n cities.
        self.visited = 0

        # Lower bound for pruning; total_cost below is only the actual partial-route distance.
        self.cost = 0
        self.total_cost = 0

    def __lt__(self, other):
        """Order search nodes by lower bound for the priority queue."""
        return self.cost < other.cost
