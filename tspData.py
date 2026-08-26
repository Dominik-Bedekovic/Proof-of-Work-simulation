from tspFunctions import TspFunction
from tspNode import TspNode
import utils


class TspData:

    def __init__(self, size):

        # Store the number of cities in the TSP instance.
        self.size = size

        # Generate the distance matrix.

        self.matrix = TspFunction._make_tsp_matrix(size)
        if self.size == 0:
            self.matrix = [
                [0,   420, 180, 760, 310, 590, 240, 830, 470, 690, 350, 910, 520, 270, 640],
                [420, 0,   550, 290, 810, 360, 720, 460, 930, 210, 680, 570, 340, 750, 190],
                [180, 550, 0,   640, 270, 730, 410, 520, 860, 330, 790, 450, 610, 220, 970],
                [760, 290, 640, 0,   480, 260, 690, 350, 720, 540, 230, 880, 310, 670, 430],
                [310, 810, 270, 480, 0,   620, 350, 740, 290, 850, 410, 530, 760, 180, 690],
                [590, 360, 730, 260, 620, 0,   470, 810, 530, 340, 720, 280, 650, 490, 370],
                [240, 720, 410, 690, 350, 470, 0,   380, 670, 290, 560, 740, 210, 830, 450],
                [830, 460, 520, 350, 740, 810, 380, 0,   430, 610, 270, 690, 580, 320, 760],
                [470, 930, 860, 720, 290, 530, 670, 430, 0,   510, 360, 780, 250, 640, 410],
                [690, 210, 330, 540, 850, 340, 290, 610, 510, 0,   630, 470, 820, 360, 550],
                [350, 680, 790, 230, 410, 720, 560, 270, 360, 630, 0,   590, 440, 710, 280],
                [910, 570, 450, 880, 530, 280, 740, 690, 780, 470, 590, 0,   360, 620, 490],
                [520, 340, 610, 310, 760, 650, 210, 580, 250, 820, 440, 360, 0,   730, 190],
                [270, 750, 220, 670, 180, 490, 830, 320, 640, 360, 710, 620, 730, 0,   540],
                [640, 190, 970, 430, 690, 370, 450, 760, 410, 550, 280, 490, 190, 540, 0]
            ]

            self.size = len(self.matrix)

        # Reduce the initial matrix and calculate its reduction cost.
        self.reduced_matrix, self.cost = (
            TspFunction._matrix_reduction(self.matrix)
        )

        # Priority queue containing nodes that still need to be explored.
        self.priority_queue = []

        # Initially, no complete tour has been found.
        self.best_cost = utils.inf
        self.best_path = []

        # Create the root node.
        self.tsp_root = TspNode(self.size)

        # Assign the reduced matrix to the root node.
        self.tsp_root.matrix = [
            row[:] for row in self.reduced_matrix
        ]

        # Search starts from city 0.
        self.tsp_root.path.append(0)

        # Set the root lower bound.
        self.tsp_root.cost = self.cost

        # Add root to priority queue.
        self.priority_queue.append(self.tsp_root)

        self.best_node = None