from tspFunctions import TspFunction
from tspNode import TspNode
import utils


class TspData:

    def __init__(self, size):
        # Store the number of cities in the TSP instance.
        self.size = size

        # Generate the distance matrix representing the complete graph.
        self.matrix = TspFunction._make_tsp_matrix(size)

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

        # The search starts from the first city which is 0.
        self.tsp_root.path.append(0)

        # Set the lower-bound cost of the root node.
        self.tsp_root.cost = self.cost

        # Add the root node to the priority queue so that the
        # search can begin.
        self.priority_queue.append(self.tsp_root)