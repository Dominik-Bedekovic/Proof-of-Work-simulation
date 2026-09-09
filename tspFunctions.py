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

        # Obtain the actual distance between the two cities from
        # the original, non-reduced matrix.
        actual_edge_cost = original_matrix[starting_city][destination_city]
        reduced_edge_cost = parent.matrix[starting_city][destination_city]

        child.path = parent.path + [destination_city]

        child.visited = parent.visited + 1

        child.vertex = destination_city

        # Disable all outgoing connections from the starting city.
        for column in range(child.size):
            child.matrix[starting_city][column] = utils.inf

        # Disable all incoming connections to the destination city.
        for row in range(child.size):
            child.matrix[row][destination_city] = utils.inf

        # Prevent the immediate return to the starting city.
        child.matrix[destination_city][0] = utils.inf

        # Reduce the new matrix and obtain the additional reduction cost.
        child.matrix, reduction_cost = TspFunction._matrix_reduction(child.matrix)

        # Calculate the lower-bound cost used for branch pruning.
        child.cost = (
            reduced_edge_cost
            + reduction_cost
            + parent.cost
        )

        # Calculate the actual cost of the path found so far.
        child.total_cost = (
            actual_edge_cost
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
        search_rate=None,
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

        # Simulated time required for the search and
        # transcript generation.
        time = 0.0

        # Process only a limited number of search nodes.
        # This simulates the search rate of an individual PoUW node.
        while search_rate is None or computations < search_rate:

            # If no nodes remain, the complete search space has
            # been explored.
            if not priority_queue:
                return computations, work, time, True

            # Select the unexplored node with the smallest
            # lower bound.
            current_node: TspNode = heapq.heappop(
                priority_queue
            )

            computations += 1
            work += 1.0

            # =====================================================
            # POP-TIME PRUNING
            # =====================================================

            # If the lower bound is already greater than or equal
            # to the best complete solution found so far, this
            # branch cannot improve the incumbent solution.
            if current_node.cost >= tsp.best_cost:

                if transcript is not None:

                    data = transcript.create_prune_data(
                        path=current_node.path,
                        vertex=current_node.vertex,
                        lower_bound=current_node.cost,
                        incumbent_cost=tsp.best_cost
                    )

                    transcript.add_step(data)

                    # Account for transcript-generation work.
                    if transcript_ratio > 0:
                        work += 1 / transcript_ratio
                        time += 1 / (transcript_ratio * search_rate)

                continue

            # =====================================================
            # COMPLETE TOUR
            # =====================================================

            # If every city has already been visited, only the
            # return edge to city 0 remains.
            if current_node.visited == levels - 1:

                final_edge = tsp.matrix[
                    current_node.vertex
                ][0]

                # No valid Hamiltonian cycle exists through this
                # node if the return edge is unavailable.
                if final_edge == utils.inf:

                    if transcript is not None:

                        data = transcript.create_dead_end_data(
                            path=current_node.path,
                            vertex=current_node.vertex,
                            lower_bound=current_node.cost,
                            incumbent_cost=tsp.best_cost,
                            reason="no_return_edge"
                        )

                        transcript.add_step(data)

                        if transcript_ratio > 0:

                            work += 1 / transcript_ratio

                            time += (
                                1
                                / (
                                    transcript_ratio
                                    * search_rate
                                )
                            )

                    continue

                total_cost = (
                    current_node.total_cost
                    + final_edge
                )

                # Important:
                # save the incumbent BEFORE potentially updating it.
                # This is the value that existed when this complete
                # tour was discovered.
                incumbent_cost = tsp.best_cost

                # Record the completed tour separately from a
                # normal B&B branch expansion.
                if transcript is not None:

                    data = transcript.create_complete_data(
                        parent_path=current_node.path,
                        parent_vertex=current_node.vertex,
                        parent_lower_bound=current_node.cost,
                        child_path=current_node.path + [0],
                        edge_cost=final_edge,
                        incumbent_cost=incumbent_cost
                    )

                    transcript.add_step(data)

                    if transcript_ratio > 0:
                        work += 1 / transcript_ratio
                        time += 1 / (transcript_ratio * search_rate)

                # Update the incumbent if this completed tour
                # is better than the previous best solution.
                if total_cost < tsp.best_cost:

                    tsp.best_cost = total_cost
                    tsp.best_path = (
                        current_node.path + [0]
                    )
                    tsp.best_node = current_node

                continue

            # =====================================================
            # NORMAL B&B EXPANSION
            # =====================================================

            # Generate one child for every legal unvisited city.
            for neighbour_node in range(
                current_node.size
            ):

                # Ignore edges that are unavailable in the
                # reduced matrix.
                if (
                    current_node.matrix[
                        current_node.vertex
                    ][neighbour_node]
                    == utils.inf
                ):
                    continue

                # Already visited cities cannot be selected again.
                if neighbour_node in current_node.path:
                    continue

                # Independently create the B&B child.
                child = TspFunction._create_child(
                    current_node,
                    tsp.matrix,
                    current_node.vertex,
                    neighbour_node
                )

                # Save the incumbent that existed when this child
                # was generated.
                incumbent_cost = tsp.best_cost

                # Determine whether this child is immediately
                # pruned by the current incumbent.
                pruned = (
                    child.cost >= incumbent_cost
                )

                # =================================================
                # TRANSCRIPT BRANCH RECORD
                # =================================================

                if transcript is not None:

                    # Actual TSP edge cost.
                    edge_cost = tsp.matrix[
                        current_node.vertex
                    ][neighbour_node]

                    # Reduced edge cost used by Little's
                    # Branch and Bound lower-bound calculation.
                    reduced_edge_cost = (
                        current_node.matrix[
                            current_node.vertex
                        ][neighbour_node]
                    )

                    # Additional matrix reduction introduced
                    # when constructing the child.
                    reduction_cost = (
                        child.cost
                        - current_node.cost
                        - reduced_edge_cost
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
                        incumbent_cost=incumbent_cost,
                        pruned=pruned
                    )

                    transcript.add_step(data)

                    # Account for transcript-generation work.
                    if transcript_ratio > 0:
                        work += 1 / transcript_ratio
                        time += 1 / (transcript_ratio * search_rate)

                # =================================================
                # GENERATION-TIME PRUNING
                # =================================================

                # Only children whose lower bound is strictly
                # smaller than the incumbent remain in the queue.
                if not pruned:
                    heapq.heappush(
                        priority_queue,
                        child
                    )

        # The search is finished if processing this batch
        # exhausted the priority queue.
        return computations, work, time, not priority_queue