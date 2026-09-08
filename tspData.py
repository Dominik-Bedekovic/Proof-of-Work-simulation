import random

from tspFunctions import TspFunction
from tspNode import TspNode
import utils


class TspData:

    def __init__(self, size, benchmark=False):

        # Store the number of cities in the TSP instance.
        self.size = size

        # =====================================================
        # BENCHMARK MATRIX
        # =====================================================
        if benchmark:

            # Local deterministic random generator.
            # This does not affect randomness elsewhere
            # in the simulation.
            rng = random.Random(12345)

            # Create an empty symmetric TSP matrix.
            self.matrix = [
                [utils.inf for _ in range(size)]
                for _ in range(size)
            ]

            # Generate one distance for each undirected edge.
            for i in range(size):
                for j in range(i + 1, size):

                    value = rng.randint(10, 1000)

                    self.matrix[i][j] = value
                    self.matrix[j][i] = value

        # =====================================================
        # NORMAL SIMULATION MATRIX
        # =====================================================
        else:

            # Generate a random TSP matrix for the simulation.
            self.matrix = TspFunction._make_tsp_matrix(size)

        # Store the actual number of cities.
        self.size = len(self.matrix)

        # Reduce the initial matrix and calculate its reduction cost.
        # The reduction cost is used as the initial lower bound.
        self.reduced_matrix, self.cost = (
            TspFunction._matrix_reduction(self.matrix)
        )

        # Priority queue containing nodes that still need to be explored.
        self.priority_queue = []

        # Initially, no complete tour has been found.
        self.best_cost = utils.inf
        self.best_path = []

        # Create the root node of the Branch and Bound search tree.
        self.tsp_root = TspNode(self.size)

        # Assign the reduced matrix to the root node.
        self.tsp_root.matrix = [
            row[:] for row in self.reduced_matrix
        ]

        # The search starts from city 0.
        self.tsp_root.path.append(0)

        # Set the lower-bound cost of the root node.
        self.tsp_root.cost = self.cost

        # Add the root node to the priority queue.
        self.priority_queue.append(self.tsp_root)

        self.best_node = None