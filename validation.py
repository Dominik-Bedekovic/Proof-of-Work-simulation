from tspData import TspData
from tspFunctions import TspFunction
import multiprocessing
import queue
import utils
import time 

def council_validation(tsp: TspData, council, proposed_path, proposed_cost):

    arguments = [(tsp, proposed_path, proposed_cost) for _ in council]

    with multiprocessing.Pool() as pool:

        results = pool.map(_validate_node, arguments)

    initial_votes = sum(results)

    ultimate_votes, ultimate_voters = _parallel_branch_validation(tsp, council, proposed_cost)

    total_votes = len(council)

    print("Council votes: ")
    print(f"Initial votes: {initial_votes}")
    print(f"Ultimate voter: {ultimate_voters}")
    print(f"Ultimate votes: {ultimate_votes}")
    print(f"Total votes: {total_votes}")

    if not _council_voting(initial_votes, ultimate_votes, total_votes, ultimate_voters):
        return False

    return True

def _validate_node(args):

    tsp, proposed_path, proposed_cost = args

    valid = True

    if proposed_path[0] != 0 or proposed_path[-1] != 0:
        valid = False

    elif len(proposed_path) != tsp.size + 1:
        valid = False

    elif len(set(proposed_path[:-1])) != tsp.size:
        valid = False

    else:

        total_cost = 0

        for i in range(len(proposed_path) - 1):

            source = proposed_path[i]
            destination = proposed_path[i + 1]

            edge_cost = tsp.matrix[source][destination]

            if edge_cost == utils.inf:
                valid = False
                break

            total_cost += edge_cost

        if total_cost != proposed_cost:
            valid = False

    return valid

def _parallel_branch_validation(tsp, council, proposed_cost):

    branches = TspFunction.create_initial_branches(tsp)

    manager = multiprocessing.Manager()

    branch_queue = manager.Queue()
    result_queue = manager.Queue()

    for branch in branches:
        branch_queue.put(branch)

    processes = []

    for node_index in range(len(council)):

        process = multiprocessing.Process(
            target=_branch_worker,
            args=(
                node_index,
                tsp,
                branch_queue,
                result_queue,
                proposed_cost
            )
        )

        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    results = []

    while not result_queue.empty():
        results.append(result_queue.get())

    manager.shutdown()

    ultimate_votes = 0
    ultimate_voters = 0

    for node_index, valid, branches_checked in results:

        if branches_checked == 0:
            print(
                f"Node {node_index + 1}: "
                f"0 branches checked, NO VOTE"
            )
            continue

        ultimate_voters += 1

        print(
            f"Node {node_index + 1}: "
            f"{branches_checked} branches checked, "
            f"vote = {valid}"
            )

        if valid:
            ultimate_votes += 1

    return ultimate_votes, ultimate_voters

def _branch_worker(node_index, tsp, branch_queue, result_queue, proposed_cost):

    valid = True
    branches_checked = 0

    while True:

        try: 
            branch = branch_queue.get_nowait()
        except queue.Empty:
            break

        branches_checked += 1

        branch_valid = TspFunction.validate_branch(tsp, branch, proposed_cost)

        if not branch_valid:
            valid = False

    result_queue.put((node_index, valid, branches_checked))


def _council_voting(initial_votes, ultimate_votes, total_votes, ultimate_voters):

    vote_ratio_initial = initial_votes / total_votes

    print(f"Initial vote ratio: {vote_ratio_initial}")

    if ultimate_voters == 0:
        return False

    vote_ratio_ultimate = ultimate_votes / ultimate_voters

    print(f"Ultimate vote ratio: {vote_ratio_ultimate}")

    if (vote_ratio_initial < 0.5 or vote_ratio_ultimate < 0.5):
        return False

    return True
    