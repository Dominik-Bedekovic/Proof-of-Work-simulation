from tspData import TspData
from tspFunctions import TspFunction
from transcript import Transcript
import multiprocessing
import queue
import utils


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

def proof_based_validation(
    tsp,
    path,
    proposed_cost,
    transcript
):

    if transcript is None:
        print("[VALIDATOR] No transcript provided.")
        return False

    # Validate the transcript hash chain.
    if not _parallel_hash_validation(
        transcript,
        num_validators=4
    ):
        print(
            "[VALIDATOR] Transcript validation failed."
        )
        return False

    # Validate the claimed final path.
    if not _validate_calculated_path(
        tsp,
        path,
        proposed_cost,
        transcript
    ):
        print(
            "[VALIDATOR] Final path is invalid."
        )
        return False

    print(
        "[VALIDATOR] Proof-based validation successful."
    )

    return True

def _validate_calculated_path(tsp, path, proposed_cost, transcript: Transcript):

    total_cost = 0

    for i in range(len(path) - 1):

        source = path[i]
        destination = path[i + 1]

        expected_edge_cost = tsp.matrix[source][destination]

        total_cost += expected_edge_cost

        print(
            f"[VALIDATOR] Checking edge "
            f"{source} -> {destination}"
        )

        # O(1) lookup using (parent path, selected neighbour)
        key = (
            tuple(path[:i + 1]),
            destination
        )

        data = transcript.path_index.get(key)

        if data is None:
            print(
                f"[VALIDATOR] Edge {source} -> {destination} "
                f"was not found in transcript."
            )
            return False

        if data["edge_cost"] != expected_edge_cost:
            print(
                f"[VALIDATOR] Edge cost mismatch for "
                f"{source} -> {destination}: "
                f"recorded={data['edge_cost']}, "
                f"expected={expected_edge_cost}"
            )
            return False

        expected_child_path = path[:i + 2]

        if data["child_path"] != expected_child_path:
            print(
                f"[VALIDATOR] Child path mismatch for "
                f"{source} -> {destination}: "
                f"recorded={data['child_path']}, "
                f"expected={expected_child_path}"
            )
            return False

        print(
            f"[VALIDATOR] ✓ Edge {source} -> {destination} "
            f"cost={expected_edge_cost}"
        )

    if total_cost != proposed_cost:
        print(
            f"[VALIDATOR] Total cost mismatch: "
            f"calculated={total_cost}, "
            f"proposed={proposed_cost}"
        )
        return False

    print(
        f"[VALIDATOR] ✓ Total path cost = {total_cost}"
    )

    print("[VALIDATOR] Optimal path validation successful.")

    return True

def _parallel_hash_validation(transcript, num_validators):

    if transcript is None:
        print("[VALIDATOR] No transcript provided.")
        return False

    steps = transcript.steps
    total_steps = len(steps)

    if total_steps == 0:
        print("[VALIDATOR] Transcript contains no steps.")
        return False

    # Do not create more validators than there are steps.
    num_validators = min(
        num_validators,
        total_steps
    )

    # Calculate the hash that comes before the
    # first transcript step.
    initial_hash = utils.create_hash(
        transcript.sigma
    )

    arguments = []

    base_size = total_steps // num_validators
    remainder = total_steps % num_validators

    current_index = 0

    for node_index in range(num_validators):

        # Distribute the remainder between the first
        # few validators.
        slice_size = base_size

        if node_index < remainder:
            slice_size += 1

        start_index = current_index
        end_index = start_index + slice_size

        # The first validator starts with hash(sigma).
        if start_index == 0:
            slice_initial_hash = initial_hash

        # Every other validator starts with the hash
        # stored by the step immediately before its slice.
        else:
            slice_initial_hash = steps[
                start_index - 1
            ]["hash"]

        arguments.append(
            (
                node_index,
                steps,
                start_index,
                end_index,
                slice_initial_hash
            )
        )

        current_index = end_index

    with multiprocessing.Pool(
        processes=num_validators
    ) as pool:

        results = pool.map(
            _hash_slice_worker,
            arguments
        )

    print("\n[VALIDATOR] Hash-chain validation:")

    all_valid = True

    for (
        node_index,
        valid,
        steps_checked,
        failed_index
    ) in results:

        if valid:

            print(
                f"Node {node_index + 1}: "
                f"{steps_checked} steps checked, "
                f"VALID"
            )

        else:

            print(
                f"Node {node_index + 1}: "
                f"hash validation FAILED at "
                f"step {failed_index}"
            )

            all_valid = False

    if all_valid:

        print(
            "[VALIDATOR] Hash chain is valid."
        )

    else:

        print(
            "[VALIDATOR] Hash chain is INVALID."
        )

    return all_valid

def _hash_slice_worker(args):
    (
        node_index,
        steps,
        start_index,
        end_index,
        initial_hash
    ) = args

    previous_hash = initial_hash
    steps_checked = 0

    for index in range(start_index, end_index):

        step = steps[index]

        expected_step_number = index + 1

        if step["step"] != expected_step_number:
            return (
                node_index,
                False,
                steps_checked,
                index
            )

        # Check that this step points to the hash
        # of the previous step.
        if step["previous_hash"] != previous_hash:
            return (
                node_index,
                False,
                steps_checked,
                index
            )

        # Recalculate this step's hash.
        hash_data = (
            previous_hash
            + str(step["step"])
            + str(step["data"])
        )

        expected_hash = utils.create_hash(
            hash_data
        )

        # Compare the calculated hash with
        # the hash stored in the transcript.
        if step["hash"] != expected_hash:
            return (
                node_index,
                False,
                steps_checked,
                index
            )

        previous_hash = step["hash"]
        steps_checked += 1

    return (
        node_index,
        True,
        steps_checked,
        None
    )