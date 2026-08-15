import utils

class TspNode:

    def __init__(self, size=0):
        self.size = size
        self.matrix = [[utils.inf] * self.size for _ in range(self.size)]
        self.path = []
        self.cost = 0
        self.vertex = 0

    def __lt__(self, other):
        return self.cost < other.cost