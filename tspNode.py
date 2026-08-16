import utils

class TspNode:

    def __init__(self, size=0):
        self.size = size
        self.matrix = [[utils.inf] * self.size for _ in range(self.size)]
        self.path = []

        self.vertex = 0
        self.visited = 0

        self.cost = 0
        self.total_cost = 0

    def __lt__(self, other):
        return self.cost < other.cost