import utils


class TspNode:

    def __init__(self, size=0):
        # Number of cities in the TSP instance.
        self.size = size

        # Reduced cost matrix used by the Branch and Bound algorithm.
        self.matrix = [
            [utils.inf] * self.size
            for _ in range(self.size)
        ]

        # List of cities visited along the current path.
        self.path = []

        # City represented by the current node.
        self.vertex = 0

        # Number of cities visited along the current path.
        self.visited = 0

        # Lower-bound cost of the current branch.
        # This value is used to determine whether the branch
        # can be pruned.
        self.cost = 0

        # Actual accumulated distance of the current path.
        self.total_cost = 0

    def __lt__(self, other):
        # Define comparison between nodes so that heapq can
        # order the priority queue according to the lower-bound cost.
        return self.cost < other.cost