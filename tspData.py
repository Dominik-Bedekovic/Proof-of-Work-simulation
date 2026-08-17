from tspFunctions import TspFunction
from tspNode import TspNode
import utils

class TspData:

    def __init__(self, size):
        self.size = size
        self.matrix = TspFunction._make_tsp_matrix(size)

        self.reduced_matrix, self.cost = TspFunction._matrix_reduction(self.matrix)
        self.priority_queue = []

        self.best_cost = utils.inf
        self.best_path = []

        self.tsp_root = TspNode(self.size)
        self.tsp_root.matrix = [row[:] for row in self.reduced_matrix] 
        self.tsp_root.path.append(0)
        self.tsp_root.cost = self.cost

        self.priority_queue.append(self.tsp_root)