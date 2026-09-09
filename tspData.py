"""Initialize a TSP instance, its reduced root matrix, and its search state."""

import random
from tspFunctions import TspFunction
from tspNode import TspNode
import utils


class TspData:
    """A distance matrix and the mutable state of its branch-and-bound search."""

    def __init__(self, size, benchmark=False):
        """Generate a matrix, reduce its root, and initialize an empty incumbent and
        search queue.
        """
        self.size = size
        if benchmark:

            # A local deterministic generator makes calibration repeatable without reseeding simulations.
            rng = random.Random(12345)
            self.matrix = [[utils.inf for _ in range(size)] for _ in range(size)]
            for i in range(size):
                for j in range(i + 1, size):
                    value = rng.randint(10, 1000)
                    self.matrix[i][j] = value
                    self.matrix[j][i] = value
        else:
            self.matrix = TspFunction._make_tsp_matrix(size)
        self.size = len(self.matrix)

        # The root reduction is the initial lower bound; the original matrix remains intact.
        self.reduced_matrix, self.cost = TspFunction._matrix_reduction(self.matrix)
        self.priority_queue = []

        # No incumbent exists until the search completes a finite tour.
        self.best_cost = utils.inf
        self.best_path = []
        self.tsp_root = TspNode(self.size)
        self.tsp_root.matrix = [row[:] for row in self.reduced_matrix]
        self.tsp_root.path.append(0)
        self.tsp_root.cost = self.cost
        self.priority_queue.append(self.tsp_root)
        self.best_node = None
