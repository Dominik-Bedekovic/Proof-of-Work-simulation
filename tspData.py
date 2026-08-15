from tspFunctions import TspFunction

class TspData:

    def __init__(self, size):
        self.size = size
        self.matrix = TspFunction._make_tsp_matrix(size)

        self.reduced_matrix, self.cost = TspFunction._matrix_reduction(self.matrix)
        self.priority_queue = []

