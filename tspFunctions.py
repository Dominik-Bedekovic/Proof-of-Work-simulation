import utils
from tspNode import TspNode

class TspFunction():

    @staticmethod
    def _make_tsp_matrix(size):

        matrix = [[utils.inf for _ in range(size)] for _ in range(size)]
        #print("First matrix: " + str(matrix))
        #print("size: " + str(size))

        for row in range(size):
            for column in range(row+1, size):

                random_decimal = pow(10, utils.random_num(1, 2))

                distance = utils.random_num(1, 9) * random_decimal

                if random_decimal == 100:

                    rng = utils.random_num(1, 4)

                    if (rng == 1):
                        distance += utils.random_num(1, 9) * 10 

                matrix[row][column] = distance
                #print(matrix[row][column])
                matrix[column][row] = distance
                #print(matrix[column][row])

        #print("Tsp function: " + str(matrix))
        return matrix
        #return tuple(tuple(row) for row in matrix)

    @staticmethod
    def _matrix_reduction(matrix):

        total_reduction_cost = 0

        matrix_len = len(matrix)

        reduced_matrix = [row[:] for row in matrix]

        reduced_matrix, total_reduction_cost = TspFunction._row_reduction(reduced_matrix, matrix_len, total_reduction_cost)

        transposed_matrix = [list(column) for column in zip(*reduced_matrix)]

        transposed_matrix, total_reduction_cost = TspFunction._row_reduction(transposed_matrix, matrix_len, total_reduction_cost)

        reduced_matrix = [list(column) for column in zip(*transposed_matrix)]

        #print(self.matrix)
        #print(transposed_matrix)
        return reduced_matrix, total_reduction_cost

    @staticmethod
    def _row_reduction(reduced_matrix, matrix_len, total_reduction_cost):

        for i in range(matrix_len):

            
            row_min = min(reduced_matrix[i])

            if row_min == utils.inf:
                continue
                 

            total_reduction_cost += row_min

            #print("ROW:", i)
            #print("BEFORE:", reduced_matrix[i])
            #print("MIN:", row_min)

     
            for j in range(matrix_len):

                if reduced_matrix[i][j] != utils.inf:
                    reduced_matrix[i][j] -= row_min

            #print("AFTER:", reduced_matrix[i])

        return reduced_matrix, total_reduction_cost

    @staticmethod
    def create_child(parent: TspNode, original_matrix, starting_city, destination_city):

        child = TspNode(parent.size)
        child.matrix = [row[:] for row in parent.matrix]

        for column in range(child.size):
            child.matrix[starting_city][column] = utils.inf

        for row in range(child.size):
            child.matrix[row][destination_city] = utils.inf

            child.matrix[destination_city][starting_city] = utils.inf

        edge_cost = original_matrix[starting_city][destination_city] 

        child.matrix, reduction_cost = TspFunction._matrix_reduction(child.matrix)

        child.cost = edge_cost + reduction_cost + parent.cost
        child.vertex = destination_city
        child.path = parent.path + [destination_city]

        return child