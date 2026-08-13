import utils

class TspData:

    def __init__(self, size):
        self.size = size
        self.matrix = self._make_tsp_matrix()

    def _make_tsp_matrix(self):

        matrix = [[utils.inf for _ in range(self.size)] for _ in range(self.size)]

        for row in range (self.size):
            for column in range(row+1, self.size):

                random_decimal = pow(10, utils.random_num(1, 2))

                distance = utils.random_num(1, 9) * random_decimal

                if random_decimal == 100:

                    rng = utils.random_num(1, 4)

                    if (rng == 1):
                        distance += utils.random_num(1, 9) * 10 

                matrix[row][column] = distance
                matrix[column][row] = distance

        return tuple(tuple(row) for row in matrix)






