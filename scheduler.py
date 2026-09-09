"""Causal cooperative B&B model. See MODEL_NOTES.md for timing boundaries."""
import copy
import heapq
import math
from tspFunctions import TspFunction


def run_search(tsp, nodes, transcript=None, transcript_ratio=0.0, on_event=None):
    """Reserve tasks at dispatch; commit search effects at search completion.

    Logging occupies the producing worker after search completion. Search effects
    are then available, but validation waits for ALL logging and search events.
    The shared hash chain serializes append service in search-completion order.
    All dispatched work is drained; no partial/in-flight work is discarded.
    """
    if not nodes or any(not math.isfinite(n.search_rate) or n.search_rate <= 0 for n in nodes):
        raise ValueError('Every search rate must be finite and positive.')
    if transcript is not None and (not math.isfinite(transcript_ratio) or transcript_ratio <= 0):
        raise ValueError('Transcript throughput ratio must be finite and positive.')
    ready = tsp.priority_queue
    heapq.heapify(ready)
    idle = set(range(len(nodes)))
    events = []
    now = 0.0
    finishing = discovering = None
    records = 0
    log_available = 0.0

    def emit(kind, index, task=None):
        if on_event is not None:
            on_event(kind, now, nodes[index], task)

    def dispatch():
        for index in sorted(idle.copy()):
            if not ready:
                break
            task = heapq.heappop(ready)
            idle.remove(index)
            emit('dispatch', index, task)
            heapq.heappush(events, (now + 1.0 / nodes[index].search_rate, index, 'search', task))

    dispatch()
    while events:
        now = events[0][0]
        # Process all existing events at the same time, worker-index order,
        # before dispatching newly available tasks.
        batch = []
        while events and events[0][0] == now:
            batch.append(heapq.heappop(events))
        for _, index, kind, task in batch:
            node = nodes[index]
            finishing = node
            if kind == 'logging':
                emit('logging_complete', index, task)
                idle.add(index)
                continue

            # Only this reserved task is processed. Other ready tasks cannot
            # accidentally be consumed by a worker whose task is in flight.
            local = copy.copy(tsp)
            local.priority_queue = [task]
            before = len(transcript.steps) if transcript is not None else 0
            old_cost = tsp.best_cost
            count, work, _, _ = TspFunction.tsp_solver(
                local, 1, transcript, transcript_ratio
            )
            node.computations += count
            node.work += work
            new_records = (len(transcript.steps) - before) if transcript is not None else 0
            records += new_records
            tsp.best_cost, tsp.best_path, tsp.best_node = local.best_cost, local.best_path, local.best_node
            if tsp.best_cost < old_cost:
                discovering = node
            for child in local.priority_queue:
                heapq.heappush(ready, child)
            emit('search_complete', index, task)
            if new_records:
                delay = new_records / (transcript_ratio * node.search_rate)
                # One hash chain: the next append needs the previous hash.
                # Serialize append service in logical completion order; the
                # producing worker remains occupied while waiting and logging.
                log_available = max(now, log_available) + delay
                heapq.heappush(events, (log_available, index, 'logging', task))
            else:
                idle.add(index)
        dispatch()

    if ready or finishing is None or tsp.best_node is None:
        raise RuntimeError('Search did not produce a complete tour.')
    return {'time': now, 'finishing_node': finishing,
            'discovering_node': discovering, 'transcript_records': records}
