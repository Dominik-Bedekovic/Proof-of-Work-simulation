"""Generate symmetric TSP instances and solve or validate them with Branch and Bound."""

from __future__ import annotations
from hostRuntime import check_cancelled

import heapq

import utils
from tspNode import TspNode
from typing import TYPE_CHECKING

# TspData is imported only for type checking. This avoids a runtime circular
# import while still allowing the type annotation used by tsp_solver().
if TYPE_CHECKING:
    from tspData import TspData


class TspFunction:
    """Stateless helper functions used by the TSP/PoUW implementation.

    The class contains the operations needed to:
    - generate a symmetric TSP distance matrix,
    - calculate lower bounds using row/column matrix reduction,
    - create child nodes in the Branch and Bound search tree,
    - reconstruct and validate Council branches, and
    - execute the main Branch and Bound solver while optionally producing
      a Proof Validation transcript.
    """

    @staticmethod
    def _make_tsp_matrix(size):
        """Generate a complete symmetric TSP matrix.

        Every pair of different cities receives a positive integer distance.
        The diagonal is kept at ``utils.inf`` because travelling from a city
        directly back to itself is not a legal TSP edge.
        """

        # Start with an NxN matrix in which every edge is unavailable.
        # Valid symmetric distances are filled in below.
        matrix = [
            [utils.inf for _ in range(size)]
            for _ in range(size)
        ]

        # Only generate values above the diagonal.
        # Each generated distance is copied to the mirrored position so that
        # matrix[a][b] == matrix[b][a].
        for row in range(size):
            for column in range(row + 1, size):

                # Generate distances mostly in tens or hundreds.
                random_decimal = pow(
                    10,
                    utils.random_num(1, 2)
                )

                distance = (
                    utils.random_num(1, 9)
                    * random_decimal
                )

                # Occasionally add a tens component to a value in the
                # hundreds range. This creates a wider variety of weights
                # instead of using only exact multiples of 100.
                if random_decimal == 100:
                    rng = utils.random_num(1, 4)

                    if rng == 1:
                        distance += (
                            utils.random_num(1, 9)
                            * 10
                        )

                # The TSP is symmetric, so the same distance is stored in
                # both directions.
                matrix[row][column] = distance
                matrix[column][row] = distance

        return matrix

    @staticmethod
    def _matrix_reduction(matrix):
        """Reduce a cost matrix and return its lower-bound contribution.

        Little-style Branch and Bound obtains a lower bound by subtracting
        the smallest finite value from every row and then every column.
        The values that were subtracted are accumulated as the reduction
        cost.

        A copy is reduced so that the caller's matrix is not modified.
        """

        # Every search node owns its own reduced matrix. Never modify the
        # parent's matrix in place because sibling branches must remain
        # independent.
        reduced_matrix = [
            row[:]
            for row in matrix
        ]

        total_reduction_cost = 0
        matrix_len = len(matrix)

        # First reduce all rows.
        reduced_matrix, total_reduction_cost = (
            TspFunction._row_reduction(
                reduced_matrix,
                matrix_len,
                total_reduction_cost
            )
        )

        # Transposing lets the same row-reduction helper operate on columns.
        # After reducing the transposed rows, transpose back to restore the
        # original matrix orientation.
        transposed_matrix = [
            list(column)
            for column in zip(*reduced_matrix)
        ]

        transposed_matrix, total_reduction_cost = (
            TspFunction._row_reduction(
                transposed_matrix,
                matrix_len,
                total_reduction_cost
            )
        )

        reduced_matrix = [
            list(column)
            for column in zip(*transposed_matrix)
        ]

        return (
            reduced_matrix,
            total_reduction_cost
        )

    @staticmethod
    def _row_reduction(
        reduced_matrix,
        matrix_len,
        total_reduction_cost
    ):
        """Reduce each row by its smallest finite value.

        The removed minimum is added to ``total_reduction_cost``. This
        accumulated reduction forms part of the Branch and Bound lower bound.
        """

        for i in range(matrix_len):

            # The minimum finite value represents the amount that can be
            # safely subtracted from this entire row.
            row_min = min(
                reduced_matrix[i]
            )

            # A row containing only infinity has no legal outgoing edge.
            # It therefore contributes no finite reduction.
            if row_min == utils.inf:
                continue

            total_reduction_cost += row_min

            # Preserve unavailable edges as infinity while subtracting the
            # row minimum from every usable edge.
            for j in range(matrix_len):
                if (
                    reduced_matrix[i][j]
                    != utils.inf
                ):
                    reduced_matrix[i][j] -= (
                        row_min
                    )

        return (
            reduced_matrix,
            total_reduction_cost
        )

    @staticmethod
    def _create_child(
        parent: TspNode,
        original_matrix,
        starting_city,
        destination_city
    ):
        """Create one Branch and Bound child node.

        Two different cost concepts are deliberately maintained:

        ``child.cost``
            The Branch and Bound lower bound. It uses the reduced edge cost
            and the new matrix-reduction cost.

        ``child.total_cost``
            The real distance travelled along the partial path. It uses the
            edge value from the original TSP matrix.

        Keeping these values separate prevents reduced-matrix values from
        being mistaken for the actual tour cost.
        """

        child = TspNode(
            parent.size
        )

        # A child receives its own copy of the parent's reduced matrix.
        child.matrix = [
            row[:]
            for row in parent.matrix
        ]

        # The original edge contributes to the real path distance.
        actual_edge_cost = (
            original_matrix[
                starting_city
            ][
                destination_city
            ]
        )

        # The reduced edge contributes to the lower-bound calculation.
        reduced_edge_cost = (
            parent.matrix[
                starting_city
            ][
                destination_city
            ]
        )

        # Extend the parent's partial route with the selected destination.
        child.path = (
            parent.path
            + [destination_city]
        )

        child.visited = (
            parent.visited
            + 1
        )

        child.vertex = (
            destination_city
        )

        # Once the path leaves starting_city, no future path can leave that
        # city again. Disable the whole source row.
        for column in range(
            child.size
        ):
            child.matrix[
                starting_city
            ][
                column
            ] = utils.inf

        # Once the path enters destination_city, no future path can enter
        # that city again. Disable the whole destination column.
        for row in range(
            child.size
        ):
            child.matrix[
                row
            ][
                destination_city
            ] = utils.inf

        # City 0 is the designated start. Returning to it before all cities
        # are visited would create an incomplete cycle, so that edge is
        # disabled during the search. Complete tours are closed later using
        # the original matrix.
        child.matrix[
            destination_city
        ][0] = utils.inf

        # Re-reduce the modified matrix. The resulting reduction is the
        # additional lower-bound contribution introduced by this branch.
        (
            child.matrix,
            reduction_cost
        ) = (
            TspFunction._matrix_reduction(
                child.matrix
            )
        )

        # IMPORTANT:
        # The lower bound uses the REDUCED edge cost, not the original edge
        # cost. Using the original edge here would double-count reductions
        # already represented in the parent bound and could cause incorrect
        # pruning.
        child.cost = (
            parent.cost
            + reduced_edge_cost
            + reduction_cost
        )

        # The real partial-tour distance is kept separately and always uses
        # the original TSP edge weight.
        child.total_cost = (
            parent.total_cost
            + actual_edge_cost
        )

        # Store the search-state information for this child.
        # These assignments intentionally mirror the values set above and
        # preserve the existing implementation exactly.
        child.vertex = (
            destination_city
        )

        child.path = (
            parent.path
            + [destination_city]
        )

        child.visited = (
            parent.visited
            + 1
        )

        return child

    @staticmethod
    def create_initial_branches(tsp):
        """Create the first-level branches used by Council Validation.

        Every branch begins at city 0 and fixes a different first edge:
        [0, 1], [0, 2], ..., [0, n-1].

        Together these branches partition all tours that start at city 0,
        allowing validators to check separate portions of the search space.
        """

        branches = []

        for city in range(
            1,
            tsp.size
        ):
            branches.append(
                [0, city]
            )

        return branches

    @staticmethod
    def create_branch(
        tsp,
        branch
    ):
        """Reconstruct the B&B node represented by a path prefix.

        Council validators receive a prefix such as [0, 3]. Rather than
        trusting any precomputed state, this function starts from the reduced
        root and independently rebuilds the branch using the same child-node
        construction logic as the solver.
        """

        # Recreate the root search node from the TSP's initial reduced matrix.
        root = TspNode(
            tsp.size
        )

        root.matrix = [
            row[:]
            for row in tsp.reduced_matrix
        ]

        root.path = [0]
        root.vertex = 0
        root.visited = 0

        # The root lower bound is the reduction cost calculated when the TSP
        # instance was initialized.
        root.cost = tsp.cost

        # No real travel distance has been accumulated at the root.
        root.total_cost = 0

        current = root

        # Replay every edge in the requested prefix. This reconstructs all
        # reduced matrices and lower bounds instead of trusting submitted
        # branch data.
        for city in branch[1:]:
            current = (
                TspFunction._create_child(
                    current,
                    tsp.matrix,
                    current.vertex,
                    city
                )
            )

        return current

    @staticmethod
    def validate_branch(
        tsp,
        branch,
        proposed_cost
    ):
        """Validate one Council search-space branch.

        The validator independently searches the branch and tries to find any
        complete tour cheaper than ``proposed_cost``.

        Returns:
            tuple:
                - True if no cheaper tour exists in this branch.
                - Number of B&B nodes processed during validation.
        """

        # Independently reconstruct the B&B state at the beginning of this
        # branch.
        branch_node = (
            TspFunction.create_branch(
                tsp,
                branch
            )
        )

        # Council Validation is not trying to rediscover the same exact path.
        # It only needs to determine whether this branch contains ANY tour
        # cheaper than the submitted optimum.
        best_cost = proposed_cost

        priority_queue = [
            branch_node
        ]

        heapq.heapify(
            priority_queue
        )

        levels = (
            tsp.tsp_root.size
        )

        # Raw validation work is counted as the number of B&B nodes popped
        # and processed by this validator.
        computations = 0

        while priority_queue:
            check_cancelled()

            # Expand the currently most promising branch according to the
            # lower-bound ordering implemented by TspNode.__lt__().
            current_node = (
                heapq.heappop(
                    priority_queue
                )
            )

            computations += 1

            # If this node cannot possibly beat the proposed solution, its
            # entire subtree is irrelevant for Council Validation.
            if (
                current_node.cost
                >= best_cost
            ):
                continue

            # A node with every city visited only needs the final edge back to
            # city 0 to become a complete Hamiltonian cycle.
            if (
                current_node.visited
                == levels - 1
            ):
                final_edge = (
                    tsp.matrix[
                        current_node.vertex
                    ][0]
                )

                # No return edge means this branch cannot form a complete tour
                # from this state.
                if final_edge == utils.inf:
                    continue

                total_cost = (
                    current_node.total_cost
                    + final_edge
                )

                # Finding a cheaper tour proves that the submitted optimum is
                # not globally optimal. Keep the cheaper value as the new
                # incumbent so that even more branches may be pruned.
                if (
                    total_cost
                    < best_cost
                ):
                    best_cost = (
                        total_cost
                    )

                continue

            # Generate every legal next city from this partial route.
            for neighbour in range(
                current_node.size
            ):

                # Infinity means this transition has been disabled by the
                # reduced-matrix constraints.
                if (
                    current_node.matrix[
                        current_node.vertex
                    ][
                        neighbour
                    ]
                    == utils.inf
                ):
                    continue

                # A Hamiltonian tour cannot visit the same city twice.
                if (
                    neighbour
                    in current_node.path
                ):
                    continue

                child = (
                    TspFunction._create_child(
                        current_node,
                        tsp.matrix,
                        current_node.vertex,
                        neighbour
                    )
                )

                # Only children whose lower bound could still improve the
                # current best cost need further exploration.
                if (
                    child.cost
                    < best_cost
                ):
                    heapq.heappush(
                        priority_queue,
                        child
                    )

        # If best_cost stayed equal to the proposal, no cheaper tour was found
        # in this branch. If it became smaller, the proposed optimum is false.
        return (
            best_cost
            >= proposed_cost,
            computations
        )

    @staticmethod
    def tsp_solver(
        tsp: TspData,
        search_rate=None,
        transcript=None,
        transcript_ratio=0
    ):
        """Process Branch and Bound nodes and optionally record a proof transcript.

        ``search_rate`` is used here as a processing limit:
        - ``None`` means process until the local queue is exhausted.
        - A numeric value limits how many B&B nodes are processed in this call.
          The cooperative scheduler normally calls this with 1 so that one
          reserved node is processed per simulated search-completion event.

        ``transcript`` is optional. When supplied, every important B&B decision
        is recorded so Proof Validation can later reconstruct and verify the
        search semantics.

        ``transcript_ratio`` expresses transcript-generation throughput relative
        to B&B-node throughput. It is used to convert transcript records into
        B&B-equivalent work for compatibility with the existing work model.

        Returns:
            tuple:
                computations:
                    Raw number of B&B nodes processed.
                work:
                    B&B-equivalent search + transcript work.
                time:
                    Transcript-generation time calculated by this local call.
                    The causal scheduler separately models when this work becomes
                    available in simulated time.
                exhausted:
                    True when this local priority queue is empty.

        The queue-exhaustion result is local to this call. The external
        scheduler additionally tracks tasks already reserved by other workers
        and outstanding transcript append service.
        """

        # This queue contains the unexplored B&B nodes available to this
        # particular solver invocation.
        priority_queue = (
            tsp.priority_queue
        )

        # Number of cities in the TSP. A node with visited == levels - 1 has
        # visited every city and only needs the edge back to city 0.
        levels = (
            tsp.tsp_root.size
        )

        # Raw B&B-node counter.
        computations = 0

        # B&B-equivalent computational work. Every processed B&B node adds one
        # unit; transcript records add fractional work according to the
        # calibrated transcript ratio.
        work = 0.0

        # Local transcript-overhead time returned for accounting. The
        # cooperative scheduler is responsible for the final causal simulated
        # completion time.
        time = 0.0

        # Process either the requested number of B&B nodes or the complete
        # local queue when search_rate is None.
        while (
            search_rate is None
            or computations < search_rate
        ):
            check_cancelled()

            # No remaining node means this local search frontier is exhausted.
            if not priority_queue:
                return (
                    computations,
                    work,
                    time,
                    True
                )

            # Branch and Bound always expands the most promising queued node
            # according to TspNode's heap ordering.
            current_node: TspNode = (
                heapq.heappop(
                    priority_queue
                )
            )

            # One popped/processed B&B node is one raw PoUW computation.
            computations += 1
            work += 1.0

            # ==============================================================
            # POP-TIME PRUNING
            # ==============================================================

            # A node may have entered the queue before a better complete tour
            # was discovered. Recheck its lower bound against the CURRENT
            # incumbent when it is actually processed.
            if (
                current_node.cost
                >= tsp.best_cost
            ):

                if transcript is not None:

                    # Record enough information for semantic replay to verify
                    # that this prune was justified by the incumbent that
                    # existed at this moment.
                    data = (
                        transcript.create_prune_data(
                            path=current_node.path,
                            vertex=current_node.vertex,
                            lower_bound=current_node.cost,
                            incumbent_cost=tsp.best_cost
                        )
                    )

                    transcript.add_step(
                        data
                    )

                    if transcript_ratio > 0:

                        # Transcript records are not counted as additional raw
                        # B&B nodes. Instead, their calibrated cost is converted
                        # into B&B-equivalent work.
                        work += (
                            1
                            / transcript_ratio
                        )

                        time += (
                            1
                            / (
                                transcript_ratio
                                * search_rate
                            )
                        )

                # A pruned node produces no children.
                continue

            # ==============================================================
            # COMPLETE TOUR
            # ==============================================================

            if (
                current_node.visited
                == levels - 1
            ):

                # The reduced search matrix deliberately prevents an early
                # return to city 0. Once every city has been visited, obtain
                # the closing edge from the ORIGINAL TSP matrix.
                final_edge = (
                    tsp.matrix[
                        current_node.vertex
                    ][0]
                )

                # If no return edge exists, this complete-looking partial path
                # is actually a dead end.
                if final_edge == utils.inf:

                    if transcript is not None:

                        data = (
                            transcript.create_dead_end_data(
                                path=current_node.path,
                                vertex=current_node.vertex,
                                lower_bound=current_node.cost,
                                incumbent_cost=tsp.best_cost,
                                reason="no_return_edge"
                            )
                        )

                        transcript.add_step(
                            data
                        )

                        if transcript_ratio > 0:
                            work += (
                                1
                                / transcript_ratio
                            )

                            time += (
                                1
                                / (
                                    transcript_ratio
                                    * search_rate
                                )
                            )

                    continue

                # Calculate the true complete-tour distance. This uses
                # total_cost, which has always been accumulated from the
                # ORIGINAL matrix rather than the reduced lower-bound matrix.
                total_cost = (
                    current_node.total_cost
                    + final_edge
                )

                # Save the incumbent BEFORE this complete tour is allowed to
                # improve it. Proof Validation uses this chronology to verify
                # that the transcript could really have occurred in this order.
                incumbent_cost = (
                    tsp.best_cost
                )

                if transcript is not None:

                    data = (
                        transcript.create_complete_data(
                            parent_path=current_node.path,
                            parent_vertex=current_node.vertex,
                            parent_lower_bound=current_node.cost,
                            child_path=current_node.path + [0],
                            edge_cost=final_edge,
                            incumbent_cost=incumbent_cost
                        )
                    )

                    transcript.add_step(
                        data
                    )

                    if transcript_ratio > 0:
                        work += (
                            1
                            / transcript_ratio
                        )

                        time += (
                            1
                            / (
                                transcript_ratio
                                * search_rate
                            )
                        )

                # A strictly cheaper complete tour becomes the new incumbent.
                # The closed route is stored with the final return to city 0.
                if (
                    total_cost
                    < tsp.best_cost
                ):
                    tsp.best_cost = (
                        total_cost
                    )

                    tsp.best_path = (
                        current_node.path
                        + [0]
                    )

                    # Keep the B&B node that discovered the winning complete
                    # tour for diagnostics/attribution.
                    tsp.best_node = (
                        current_node
                    )

                continue

            # ==============================================================
            # EXPAND PARTIAL NODE
            # ==============================================================

            # Explore every city that is still a legal next destination.
            for neighbour_node in range(
                current_node.size
            ):

                # The reduced matrix marks forbidden transitions with infinity.
                if (
                    current_node.matrix[
                        current_node.vertex
                    ][
                        neighbour_node
                    ]
                    == utils.inf
                ):
                    continue

                # Never revisit a city already contained in the partial route.
                if (
                    neighbour_node
                    in current_node.path
                ):
                    continue

                # Independently construct the child, including its reduced
                # matrix, lower bound and real partial-tour cost.
                child = (
                    TspFunction._create_child(
                        current_node,
                        tsp.matrix,
                        current_node.vertex,
                        neighbour_node
                    )
                )

                # Pruning must use the incumbent that exists at the time this
                # particular child is generated.
                incumbent_cost = (
                    tsp.best_cost
                )

                pruned = (
                    child.cost
                    >= incumbent_cost
                )

                if transcript is not None:

                    # The original edge is recorded because it is part of the
                    # real route cost.
                    edge_cost = (
                        tsp.matrix[
                            current_node.vertex
                        ][
                            neighbour_node
                        ]
                    )

                    # The reduced edge is required to independently reconstruct
                    # the child's lower-bound calculation.
                    reduced_edge_cost = (
                        current_node.matrix[
                            current_node.vertex
                        ][
                            neighbour_node
                        ]
                    )

                    # Rearranging:
                    #
                    # child.cost =
                    #     parent.cost
                    #     + reduced_edge_cost
                    #     + reduction_cost
                    #
                    # gives the additional matrix-reduction contribution stored
                    # in the transcript.
                    reduction_cost = (
                        child.cost
                        - current_node.cost
                        - reduced_edge_cost
                    )

                    # Record every legal generated child, including children
                    # that are immediately pruned. This is essential: omitting
                    # a legal child would leave part of the search space
                    # unaccounted for during semantic replay.
                    data = (
                        transcript.create_step_data(
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
                    )

                    transcript.add_step(
                        data
                    )

                    if transcript_ratio > 0:
                        work += (
                            1
                            / transcript_ratio
                        )

                        time += (
                            1
                            / (
                                transcript_ratio
                                * search_rate
                            )
                        )

                # Only branches whose lower bound can still beat the incumbent
                # remain on the search frontier.
                if not pruned:
                    heapq.heappush(
                        priority_queue,
                        child
                    )

        # If the loop stopped because search_rate B&B nodes were processed,
        # report whether this LOCAL queue is currently empty. The causal
        # scheduler may still have other tasks reserved by other workers.
        return (
            computations,
            work,
            time,
            not priority_queue
        )
