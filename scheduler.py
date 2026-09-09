"""Schedule cooperative B&B tasks and ordered transcript appends in simulated time."""

import copy
import heapq
import math
from tspFunctions import TspFunction


def run_search(tsp, nodes, transcript=None, transcript_ratio=0.0, on_event=None):
    """Reserve tasks at dispatch; commit search effects at search completion.

    Logging occupies the producing worker after search completion. Search effects
    are then available, but validation waits for ALL logging and search events. The
    shared hash chain serializes append service in search-completion order. All
    dispatched work is drained; no partial/in-flight work is discarded.
    """
    if not nodes or any(
        (not math.isfinite(n.search_rate) or n.search_rate <= 0 for n in nodes)
    ):
        raise ValueError("Every search rate must be finite and positive.")
    if transcript is not None and (
        not math.isfinite(transcript_ratio) or transcript_ratio <= 0
    ):
        raise ValueError("Transcript throughput ratio must be finite and positive.")

    # Ready tasks are separate from reserved tasks in the event heap.
    ready = tsp.priority_queue
    heapq.heapify(ready)
    idle = set(range(len(nodes)))
    events = []
    now = 0.0
    finishing = discovering = None
    records = 0
    log_available = 0.0

    def emit(kind, index, task=None):
        """Report a scheduling event to the optional observer used by tests."""
        if on_event is not None:
            on_event(kind, now, nodes[index], task)

    def dispatch():
        """Reserve available tasks for idle workers and schedule their search
        completion times.
        """
        for index in sorted(idle.copy()):
            if not ready:
                break

            # Reserve the task now; its children cannot exist before completion.
            task = heapq.heappop(ready)
            idle.remove(index)
            emit("dispatch", index, task)
            heapq.heappush(
                events, (now + 1.0 / nodes[index].search_rate, index, "search", task)
            )

    dispatch()
    while events:
        now = events[0][0]

        # Handle existing tied events in worker order before assigning new work.
        batch = []
        while events and events[0][0] == now:
            batch.append(heapq.heappop(events))
        for _, index, kind, task in batch:
            node = nodes[index]
            finishing = node
            if kind == "logging":
                emit("logging_complete", index, task)
                idle.add(index)
                continue

            # Use the current incumbent, but process only this worker's reserved task.
            local = copy.copy(tsp)
            local.priority_queue = [task]
            before = len(transcript.steps) if transcript is not None else 0
            old_cost = tsp.best_cost
            count, work, _, _ = TspFunction.tsp_solver(
                local, 1, transcript, transcript_ratio
            )
            node.computations += count
            node.work += work
            new_records = (
                len(transcript.steps) - before if transcript is not None else 0
            )
            records += new_records

            # Publish search effects only after the full search duration has elapsed.
            tsp.best_cost, tsp.best_path, tsp.best_node = (
                local.best_cost,
                local.best_path,
                local.best_node,
            )
            if tsp.best_cost < old_cost:
                discovering = node
            for child in local.priority_queue:
                heapq.heappush(ready, child)
            emit("search_complete", index, task)
            if new_records:
                delay = new_records / (transcript_ratio * node.search_rate)

                # The next append depends on the previous hash; waiting occupies the worker
                # without adding extra computational work.
                log_available = max(now, log_available) + delay
                heapq.heappush(events, (log_available, index, "logging", task))
            else:
                idle.add(index)
        dispatch()

    # All search and append events have drained before validation can begin.
    if ready or finishing is None or tsp.best_node is None:
        raise RuntimeError("Search did not produce a complete tour.")
    return {
        "time": now,
        "finishing_node": finishing,
        "discovering_node": discovering,
        "transcript_records": records,
    }
