from __future__ import annotations
import utils
import heapq
from tspNode import TspNode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tspData import TspData

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

            for j in range(matrix_len):

                if reduced_matrix[i][j] != utils.inf:
                    reduced_matrix[i][j] -= row_min

        return reduced_matrix, total_reduction_cost

    @staticmethod
    def _create_child(parent: TspNode, original_matrix, starting_city, destination_city):

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
        child.total_cost = edge_cost + parent.total_cost
        child.vertex = destination_city
        child.path = parent.path + [destination_city]
        child.visited = parent.visited + 1

        return child

    @staticmethod
    def tsp_solver(tsp: TspData, search_rate):

        priority_queue = tsp.priority_queue

        levels = tsp.tsp_root.size
        computations = 0
        for _ in range(search_rate):

            if not priority_queue:
                return computations, True
                

            current_node: TspNode = heapq.heappop(priority_queue)

            computations += 1

            if current_node.cost >= tsp.best_cost:
                continue

            if current_node.visited == levels - 1:

                final_edge = tsp.matrix[current_node.vertex][0]  

                if final_edge == utils.inf:
                    continue

                total_cost = current_node.total_cost + final_edge

                if total_cost < tsp.best_cost:
                    tsp.best_cost = total_cost
                    tsp.best_path = current_node.path + [0]

                continue

            for neighbour_node in range(current_node.size):

                if current_node.matrix[current_node.vertex][neighbour_node] != utils.inf:

                    visited = neighbour_node in current_node.path

                    if visited:
                        continue

                    child = TspFunction._create_child(current_node, tsp.matrix, current_node.vertex, neighbour_node)

                    if child.cost < tsp.best_cost:
                        heapq.heappush(priority_queue, child)

        #print(f"final matrix: {child.matrix}")
        return computations, False