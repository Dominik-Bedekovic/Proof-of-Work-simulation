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
        # Create an NxN matrix representing the complete graph.
        # Initially, all connections are set to infinity.
        matrix = [[utils.inf for _ in range(size)] for _ in range(size)]

        # Generate a distance for every pair of cities.
        # Only the upper triangular part of the matrix is generated
        # because the TSP instance is symmetric.
        for row in range(size):
            for column in range(row + 1, size):

                # Generate a random distance with one or two
                # decimal places.
                random_decimal = pow(10, utils.random_num(1, 2))
                distance = utils.random_num(1, 9) * random_decimal

                # Occasionally generate a distance with an additional
                # decimal component to increase the variety of values.
                if random_decimal == 100:
                    rng = utils.random_num(1, 4)

                    if rng == 1:
                        distance += utils.random_num(1, 9) * 10

                # Store the same distance in both directions because
                # the generated TSP instance is symmetric.
                matrix[row][column] = distance
                matrix[column][row] = distance

        return matrix


    @staticmethod
    def _matrix_reduction(matrix):
        # Create a copy so that the original matrix is not modified.
        reduced_matrix = [row[:] for row in matrix]

        total_reduction_cost = 0
        matrix_len = len(matrix)

        # First reduce all rows of the matrix.
        reduced_matrix, total_reduction_cost = TspFunction._row_reduction(
            reduced_matrix,
            matrix_len,
            total_reduction_cost
        )

        # Transpose the matrix so that the same reduction procedure
        # can be applied to its columns.
        transposed_matrix = [
            list(column) for column in zip(*reduced_matrix)
        ]

        # Reduce the columns by treating them as rows.
        transposed_matrix, total_reduction_cost = TspFunction._row_reduction(
            transposed_matrix,
            matrix_len,
            total_reduction_cost
        )

        # Transpose the matrix back to its original orientation.
        reduced_matrix = [
            list(column) for column in zip(*transposed_matrix)
        ]

        # Return the reduced matrix and the total reduction cost,
        # which contributes to the lower bound of the node.
        return reduced_matrix, total_reduction_cost


    @staticmethod
    def _row_reduction(
        reduced_matrix,
        matrix_len,
        total_reduction_cost
    ):
        # Reduce each row by subtracting its smallest finite value
        # from all other finite values in that row.
        for i in range(matrix_len):

            row_min = min(reduced_matrix[i])

            # Skip rows that contain no valid remaining connections.
            if row_min == utils.inf:
                continue

            # The selected minimum contributes to the reduction cost.
            total_reduction_cost += row_min

            for j in range(matrix_len):

                # Infinite values represent unavailable connections
                # and must not be modified.
                if reduced_matrix[i][j] != utils.inf:
                    reduced_matrix[i][j] -= row_min

        return reduced_matrix, total_reduction_cost


    @staticmethod
    def _create_child(
        parent: TspNode,
        original_matrix,
        starting_city,
        destination_city
    ):
        # Create a new node representing a possible extension
        # of the parent's path.
        child = TspNode(parent.size)

        # Copy the parent's reduced matrix.
        child.matrix = [row[:] for row in parent.matrix]

        # Disable all outgoing connections from the starting city.
        for column in range(child.size):
            child.matrix[starting_city][column] = utils.inf

        # Disable all incoming connections to the destination city.
        for row in range(child.size):
            child.matrix[row][destination_city] = utils.inf

        # Prevent the immediate return to the starting city.
        child.matrix[destination_city][starting_city] = utils.inf

        # Obtain the actual distance between the two cities from
        # the original, non-reduced matrix.
        edge_cost = original_matrix[starting_city][destination_city]

        # Reduce the new matrix and obtain the additional reduction cost.
        child.matrix, reduction_cost = TspFunction._matrix_reduction(
            child.matrix
        )

        # Calculate the lower-bound cost used for branch pruning.
        child.cost = (
            edge_cost
            + reduction_cost
            + parent.cost
        )

        # Calculate the actual cost of the path found so far.
        child.total_cost = (
            edge_cost
            + parent.total_cost
        )

        # Store information about the newly reached city and path.
        child.vertex = destination_city
        child.path = parent.path + [destination_city]
        child.visited = parent.visited + 1

        return child


    @staticmethod
    def tsp_solver(tsp: TspData, search_rate):
        # Obtain the priority queue containing nodes that still need
        # to be explored.
        priority_queue = tsp.priority_queue

        # Number of cities in the TSP instance.
        levels = tsp.tsp_root.size

        # Count the number of processed search nodes.
        computations = 0

        # Process a limited number of nodes according to the
        # simulated search rate of the current node.
        for _ in range(search_rate):

            # If the priority queue is empty, the entire search space
            # has been processed and the optimal solution is known.
            if not priority_queue:
                return computations, True

            # Select the node with the smallest lower-bound cost.
            current_node: TspNode = heapq.heappop(priority_queue)

            computations += 1

            # If the lower bound is already worse than the best
            # solution found so far, this branch can be pruned.
            if current_node.cost >= tsp.best_cost:
                continue

            # Check whether the current node has visited all cities.
            if current_node.visited == levels - 1:

                # Add the final edge returning to the starting city.
                final_edge = tsp.matrix[current_node.vertex][0]

                # Skip the path if the return connection is unavailable.
                if final_edge == utils.inf:
                    continue

                total_cost = (
                    current_node.total_cost
                    + final_edge
                )

                # Update the best known solution if this tour is shorter.
                if total_cost < tsp.best_cost:
                    tsp.best_cost = total_cost
                    tsp.best_path = current_node.path + [0]

                continue

            # Generate children for every unvisited neighbouring city.
            for neighbour_node in range(current_node.size):

                if (
                    current_node.matrix[
                        current_node.vertex
                    ][neighbour_node] != utils.inf
                ):

                    # Check whether the city has already been visited.
                    visited = neighbour_node in current_node.path

                    if visited:
                        continue

                    # Create a new branch of the search tree.
                    child = TspFunction._create_child(
                        current_node,
                        tsp.matrix,
                        current_node.vertex,
                        neighbour_node
                    )

                    # Only add the child to the priority queue if its
                    # lower bound can still lead to a better solution.
                    if child.cost < tsp.best_cost:
                        heapq.heappush(priority_queue, child)

        # The search was not completed during this execution.
        return computations, False