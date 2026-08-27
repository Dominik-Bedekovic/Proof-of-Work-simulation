from tspFunctions import TspFunction
from tspNode import TspNode
import utils


class TspData:

    def __init__(self, size, benchmark=False):

        # Store the number of cities in the TSP instance.
        self.size = size

        if benchmark:
            self.matrix = [
                [utils.inf, 20, 200, 30, 100, 200, 10, 800, 40, 10, 400],
                [20, utils.inf, 40, 620, 400, 30, 900, 930, 400, 30, 670],
                [200, 40, utils.inf, 20, 570, 800, 200, 40, 20, 10, 700],
                [30, 620, 20, utils.inf, 100, 900, 60, 100, 90, 30, 20],
                [100, 400, 570, 100, utils.inf, 30, 40, 900, 300, 200, 600],
                [200, 30, 800, 900, 30, utils.inf, 60, 80, 40, 140, 10],
                [10, 900, 200, 60, 40, 60, utils.inf, 800, 50, 20, 50],
                [800, 930, 40, 100, 900, 80, 800, utils.inf, 500, 50, 40],
                [40, 400, 20, 90, 300, 40, 50, 500, utils.inf, 60, 70],
                [10, 30, 10, 30, 200, 140, 20, 50, 60, utils.inf, 30],
                [400, 670, 700, 20, 600, 10, 50, 40, 70, 30, utils.inf]
            ]
        else:
            # Generate the distance matrix representing the complete graph.
            self.matrix = TspFunction._make_tsp_matrix(size)
                    
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

        # The search starts from the first city which is 0.
        self.tsp_root.path.append(0)

        # Set the lower-bound cost of the root node.
        self.tsp_root.cost = self.cost

        # Add the root node to the priority queue so that the
        # search can begin.
        self.priority_queue.append(self.tsp_root)

        self.best_node = None