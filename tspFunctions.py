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
    def create_initial_branches(tsp):
        # Create one initial branch for every city except the starting
        # city (0). Each branch represents the first edge of a possible
        # TSP solution, e.g. [0, 1], [0, 2], [0, 3], ...
        branches = []

        for city in range(1, tsp.size):
            branches.append([0, city])

        return branches


    @staticmethod
    def create_branch(tsp, branch):
        # Create the root node from which the selected branch
        # will be reconstructed.
        root = TspNode(tsp.size)

        # Copy the reduced cost matrix from the original TSP problem.
        # A copy is used so that modifications during the search
        # do not alter the original TSP instance.
        root.matrix = [
            row[:] for row in tsp.reduced_matrix
        ]

        # Initialize the root node.
        root.path = [0]
        root.vertex = 0
        root.visited = 0
        root.cost = tsp.cost
        root.total_cost = 0

        current = root

        # Reconstruct the selected branch by creating a child node
        # for every city contained in the branch.
        for city in branch[1:]:
            current = TspFunction._create_child(
                current,
                tsp.matrix,
                current.vertex,
                city
            )

        return current


    @staticmethod
    def validate_branch(tsp, branch, proposed_cost):
        # Reconstruct the branch as a B&B search node.
        branch_node = TspFunction.create_branch(
            tsp,
            branch
        )

        # The proposed solution is used as the initial upper bound.
        # A branch only needs to be explored if it can potentially
        # produce a solution better than the proposed cost.
        best_cost = proposed_cost

        # Use a priority queue to process the most promising B&B
        # nodes first, based on their lower-bound cost.
        priority_queue = [branch_node]
        heapq.heapify(priority_queue)

        # Number of cities that must be visited before returning
        # to the starting city.
        levels = tsp.tsp_root.size

        # Count the number of B&B nodes examined during validation.
        computations = 0

        while priority_queue:
            # Select the node with the smallest lower-bound cost.
            current_node = heapq.heappop(priority_queue)
            computations += 1

            # If the lower bound is already greater than or equal
            # to the proposed solution, this node cannot produce
            # a better solution and can therefore be pruned.
            if current_node.cost >= best_cost:
                continue

            # If all cities have been visited, check the edge that
            # returns from the current city to the starting city.
            if current_node.visited == levels - 1:

                final_edge = tsp.matrix[
                    current_node.vertex
                ][0]

                # If no edge exists back to the starting city,
                # this branch cannot form a valid Hamiltonian cycle.
                if final_edge == utils.inf:
                    continue

                # Calculate the complete cost of the discovered tour.
                total_cost = (
                    current_node.total_cost
                    + final_edge
                )

                # If this tour is better than the current best cost,
                # update the upper bound used for subsequent pruning.
                if total_cost < best_cost:
                    best_cost = total_cost

                continue

            # Expand the current node by considering every possible
            # neighbouring city.
            for neighbour in range(current_node.size):

                # Ignore edges that do not exist.
                if (
                    current_node.matrix[
                        current_node.vertex
                    ][neighbour] == utils.inf
                ):
                    continue

                # A city that is already part of the current path
                # cannot be visited again.
                if neighbour in current_node.path:
                    continue

                # Create a new B&B node by extending the current path
                # with the selected neighbouring city.
                child = TspFunction._create_child(
                    current_node,
                    tsp.matrix,
                    current_node.vertex,
                    neighbour
                )

                # Only continue searching this child if its lower
                # bound indicates that it could improve the proposed
                # solution.
                if child.cost < best_cost:
                    heapq.heappush(
                        priority_queue,
                        child
                    )

        # If the best solution found during the branch search is
        # at least as expensive as the proposed solution, no better
        # solution exists within this branch.
        return (
            best_cost >= proposed_cost,
            computations
        )

    @staticmethod
    def tsp_solver(
        tsp: TspData,
        search_rate,
        transcript=None,
        transcript_ratio=0
    ):
        # Priority queue containing all search-tree nodes
        # that have not yet been processed.
        priority_queue = tsp.priority_queue

        # Total number of cities in the TSP instance.
        levels = tsp.tsp_root.size

        # Number of search-tree nodes processed during this call.
        computations = 0

        # Simulated computational work performed during the search.
        work = 0.0

        # Simulated time required for the search and transcript generation.
        time = 0.0

        # Process only a limited number of search nodes.
        # This simulates the search rate of an individual PoUW node.
        for _ in range(search_rate):

            # If no nodes remain, the complete search space has
            # been explored and the optimal solution has been found.
            if not priority_queue:
                return computations, work, time, True

            # Select the unexplored node with the smallest lower bound.
            current_node: TspNode = heapq.heappop(priority_queue)
            computations += 1
            work += 1.0

            # If the lower bound is already greater than or equal to
            # the best complete solution found so far, this branch
            # cannot produce a better solution and is therefore pruned.
            if current_node.cost >= tsp.best_cost:
                continue

            # Check whether the current path has visited every city.
            if current_node.visited == levels - 1:

                # Add the edge returning from the final city to city 0.
                final_edge = tsp.matrix[current_node.vertex][0]

                # Ignore the path if no return edge exists.
                if final_edge == utils.inf:
                    continue

                # Calculate the total cost of the complete tour.
                total_cost = (
                    current_node.total_cost
                    + final_edge
                )

                # Record the completed path in the transcript.
                if transcript is not None:
                    data = transcript.create_step_data(
                        parent_path=current_node.path,
                        parent_vertex=current_node.vertex,
                        parent_lower_bound=current_node.cost,
                        selected_neighbour=0,
                        child_path=current_node.path + [0],
                        edge_cost=final_edge,
                        reduction_cost=None,
                        child_lower_bound=None,
                        pruned=False
                    )

                    transcript.add_step(data)

                    # Account for the additional computational work
                    # required to generate the transcript entry.
                    if transcript_ratio > 0:
                        work += 1 / transcript_ratio
                        time += 1 / transcript_ratio

                # Update the best known solution if this tour is better.
                if total_cost < tsp.best_cost:
                    tsp.best_cost = total_cost
                    tsp.best_path = current_node.path + [0]
                    tsp.best_node = current_node

                continue

            # Generate a child node for every unvisited neighbouring city.
            for neighbour_node in range(current_node.size):

                # Ignore neighbours that cannot be reached from
                # the current city.
                if (
                    current_node.matrix[
                        current_node.vertex
                    ][neighbour_node] == utils.inf
                ):
                    continue

                # A city already contained in the current path
                # must not be visited again.
                if neighbour_node in current_node.path:
                    continue

                # Create a new branch by extending the current path
                # with the selected neighbouring city.
                child = TspFunction._create_child(
                    current_node,
                    tsp.matrix,
                    current_node.vertex,
                    neighbour_node
                )

                # Record the branch expansion in the transcript.
                if transcript is not None:
                    edge_cost = tsp.matrix[
                        current_node.vertex
                    ][neighbour_node]

                    # The reduction cost represents the change in the
                    # lower bound that cannot be explained by the edge cost.
                    reduction_cost = (
                        child.cost
                        - current_node.cost
                        - edge_cost
                    )

                    data = transcript.create_step_data(
                        parent_path=current_node.path,
                        parent_vertex=current_node.vertex,
                        parent_lower_bound=current_node.cost,
                        selected_neighbour=neighbour_node,
                        child_path=child.path,
                        edge_cost=edge_cost,
                        reduction_cost=reduction_cost,
                        child_lower_bound=child.cost,
                        pruned=child.cost >= tsp.best_cost
                    )

                    transcript.add_step(data)

                    # Account for the computational work and time
                    # required to generate the transcript entry.
                    if transcript_ratio > 0:
                        work += 1 / transcript_ratio
                        time += 1 / transcript_ratio

                # Only keep the child in the priority queue if its
                # lower bound indicates that it could improve the
                # current best solution.
                if child.cost < tsp.best_cost:
                    heapq.heappush(priority_queue, child)

        # The search has not been completely explored during this call.
        # Another call can continue processing the remaining queue.
        return computations, work, time, False