import heapq
import time
import utils
from tspFunctions import TspFunction

def tsp_worker(
    node_index,
    matrix,
    levels,
    branch_queue,
    queue_lock,
    best_cost,
    best_path,
    best_lock,
    active_workers,
    finished,
    result_queue
):

    print(
        f"[NODE {node_index + 1}] Worker started",
        flush=True
    )

    computations = 0

    while not finished.is_set():

        # Get a branch
        with queue_lock:

            if branch_queue:

                queue = list(branch_queue)

                current_node = heapq.heappop(queue)

                branch_queue[:] = queue

                active_workers.value += 1

            else:

                current_node = None

        # No branch available
        if current_node is None:

            with queue_lock:

                if (
                    not branch_queue
                    and active_workers.value == 0
                ):
                    finished.set()
                    break

            time.sleep(0.001)
            continue

        computations += 1

        # Check current branch
        with best_lock:
            current_best = best_cost.value

        if current_node.cost >= current_best:

            with queue_lock:
                active_workers.value -= 1

            continue

        # Complete tour
        if current_node.visited == levels - 1:

            final_edge = matrix[
                current_node.vertex
            ][0]

            if final_edge != utils.inf:

                total_cost = (
                    current_node.total_cost
                    + final_edge
                )

                complete_path = (
                    current_node.path
                    + [0]
                )

                with best_lock:

                    if total_cost < best_cost.value:

                        best_cost.value = total_cost

                        best_path[:] = complete_path

            with queue_lock:
                active_workers.value -= 1

            continue

        # Generate children
        for neighbour in range(current_node.size):

            if neighbour in current_node.path:
                continue

            edge_cost = matrix[
                current_node.vertex
            ][neighbour]

            if edge_cost == utils.inf:
                continue

            child = TspFunction._create_child(
                current_node,
                matrix,
                current_node.vertex,
                neighbour
            )

            with best_lock:
                current_best = best_cost.value

            if child.cost >= current_best:
                continue

            with queue_lock:

                queue = list(branch_queue)

                heapq.heappush(
                    queue,
                    child
                )

                branch_queue[:] = queue

        with queue_lock:
            active_workers.value -= 1

    print(
        f"[NODE {node_index + 1}] "
        f"Finished. Computations={computations}",
        flush=True
    )

    result_queue.put(
        (
            node_index,
            computations
        )
    )