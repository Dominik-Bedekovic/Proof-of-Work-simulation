from tspData import TspData
from tspFunctions import TspFunction
from transcript import Transcript
import multiprocessing
import utils


def council_validation(tsp: TspData, council, proposed_path, proposed_cost):

    arguments = [(tsp, proposed_path, proposed_cost) for _ in council]

    with multiprocessing.Pool() as pool:

        results = pool.map(_validate_node, arguments)

    initial_votes = sum(
        valid for valid, computations in results)

    initial_computations = sum(
        computations for valid, computations in results
    )

    initial_validation_time = max(
        computations / node.validation_rate
        for node, (_, computations)
        in zip(council, results)
    )

    ultimate_votes, ultimate_voters, ultimate_computations, ultimate_validation_time = _parallel_branch_validation(tsp, council, proposed_cost)

    total_votes = len(council)

    total_computations = (initial_computations + ultimate_computations)

    total_validation_time = (
        initial_validation_time + ultimate_validation_time
    )

    print("Council votes: ")
    print(f"Initial votes: {initial_votes}")
    print(f"Ultimate voter: {ultimate_voters}")
    print(f"Ultimate votes: {ultimate_votes}")
    print(f"Total votes: {total_votes}")
    print(f"Total computations: {total_computations}")

    print(
        f"Initial validation time: "
        f"{initial_validation_time:.4f}s"
    )

    print(
        f"Ultimate validation time: "
        f"{ultimate_validation_time:.4f}s"
    )

    print(
        f"Total validation time: "
        f"{total_validation_time:.4f}s"
    )

    if not _council_voting(initial_votes, ultimate_votes, total_votes, ultimate_voters):
        return False, total_computations, total_validation_time

    return True, total_computations, total_validation_time

def _validate_node(args):

    tsp, proposed_path, proposed_cost = args

    computations = 0
    valid = True

    computations += 1
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

            computations += 1

            if edge_cost == utils.inf:
                valid = False
                break

            total_cost += edge_cost

        if total_cost != proposed_cost:
            valid = False

    return (valid, computations)

def _parallel_branch_validation(tsp, council, proposed_cost):

    branches = TspFunction.create_initial_branches(tsp)

    processes = []
    result_queue = multiprocessing.Queue()

    num_validators = len(council)

    # Divide branches among validators
    branch_slices = [
        branches[i::num_validators]
        for i in range(num_validators)
    ]

    for node_index, branch_slice in enumerate(branch_slices):

        process = multiprocessing.Process(
            target=_branch_worker,
            args=(
                node_index,
                council[node_index].validation_rate,
                tsp,
                branch_slice,
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

    ultimate_votes = 0
    ultimate_voters = 0
    ultimate_computations = 0
    ultimate_validation_time = 0

    for node_index, valid, computations, validation_rate in results:

        ultimate_computations += computations

        if computations == 0:
            print(
                f"Node {node_index + 1}: "
                f"0 branches checked, NO VOTE"
            )
            continue

        node_validation_time = (
                    computations / validation_rate
                )

        ultimate_validation_time = max(
            ultimate_validation_time,
            node_validation_time
        )

        ultimate_voters += 1

        print(
            f"Node {node_index + 1}: "
            f"{computations} computations, "
            f"vote = {valid}"
        )

        if valid:
            ultimate_votes += 1

    return (
        ultimate_votes,
        ultimate_voters,
        ultimate_computations,
        ultimate_validation_time
    )

def _branch_worker(
    node_index,
    validation_rate,
    tsp,
    branches,
    result_queue,
    proposed_cost
):

    valid = True
    computations = 0

    for branch in branches:

        branch_valid, branch_computations = (
            TspFunction.validate_branch(
                tsp,
                branch,
                proposed_cost
            )
        )

        computations += branch_computations

        if not branch_valid:
            valid = False

    result_queue.put(
        (node_index, valid, computations, validation_rate)
    )

def _council_voting(initial_votes, ultimate_votes, total_votes, ultimate_voters):

    vote_ratio_initial = initial_votes / total_votes

    print(f"Initial vote ratio: {vote_ratio_initial}")

    if ultimate_voters == 0:
        print("HEYYYY LISTTEEENNN")
        return False

    vote_ratio_ultimate = ultimate_votes / ultimate_voters


    if vote_ratio_initial and vote_ratio_ultimate:
        return True

    print(f"Ultimate vote ratio: {vote_ratio_ultimate}")

    return False

def proof_based_validation(
    tsp,
    path,
    proposed_cost,
    transcript,
    validators
):
    """
    Validate a PoUW solution using:

    1. Parallel transcript hash-chain validation.
    2. Parallel validation of the claimed path.

    Returns:
        (valid, total_computations, total_time)
    """

    if transcript is None:
        print("[VALIDATOR] No transcript provided.")
        return False, 0, 0.0

    if not validators:
        print("[VALIDATOR] No validators available.")
        return False, 0, 0.0

    # ---------------------------------------------------------
    # 1. Validate transcript hash chain.
    # ---------------------------------------------------------

    (
        hash_valid,
        hash_computations,
        hash_time
    ) = _parallel_hash_validation(
        transcript,
        validators
    )

    if not hash_valid:
        print(
            "[VALIDATOR] Transcript validation failed."
        )
        return False, hash_computations, hash_time

    # ---------------------------------------------------------
    # 2. Validate the claimed final path.
    # ---------------------------------------------------------

    (
        path_valid,
        path_computations,
        path_time
    ) = _parallel_path_validation(
        tsp,
        path,
        proposed_cost,
        transcript,
        validators
    )

    if not path_valid:
        print(
            "[VALIDATOR] Final path is invalid."
        )

        return (
            False,
            hash_computations + path_computations,
            hash_time + path_time
        )

    total_computations = (
        hash_computations
        + path_computations
    )

    total_time = (
        hash_time
        + path_time
    )

    print(
        "[VALIDATOR] Proof-based validation successful."
    )

    print(
        f"[VALIDATOR] Validation computations: "
        f"{total_computations}"
    )

    print(
        f"[VALIDATOR] Validation time: "
        f"{total_time:.4f}s"
    )

    return (
        True,
        total_computations,
        total_time
    )


def _parallel_hash_validation(
    transcript,
    validators
):
    """
    Split the transcript between validators.

    Each transcript step requires one hash validation
    computation.

    Validators operate in parallel, so validation time is
    determined by the slowest validator.
    """

    if transcript is None:
        print("[VALIDATOR] No transcript provided.")
        return False, 0, 0.0

    steps = transcript.steps
    total_steps = len(steps)

    if total_steps == 0:
        print(
            "[VALIDATOR] Transcript contains no steps."
        )
        return False, 0, 0.0

    # Do not use more validators than there are steps.
    validators = validators[:min(
        len(validators),
        total_steps
    )]

    num_validators = len(validators)

    initial_hash = utils.create_hash(
        transcript.sigma
    )

    arguments = []

    base_size = (
        total_steps // num_validators
    )

    remainder = (
        total_steps % num_validators
    )

    current_index = 0

    for validator_index, validator in enumerate(
        validators
    ):
        slice_size = base_size

        if validator_index < remainder:
            slice_size += 1

        start_index = current_index
        end_index = (
            start_index + slice_size
        )

        # First validator starts from hash(sigma).
        if start_index == 0:
            slice_initial_hash = initial_hash

        # Other validators start from the hash
        # immediately before their assigned slice.
        else:
            slice_initial_hash = steps[
                start_index - 1
            ]["hash"]

        arguments.append(
            (
                validator_index,
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

    print(
        "\n[VALIDATOR] Hash-chain validation:"
    )

    all_valid = True
    total_computations = 0
    validator_times = []

    for (
        validator_index,
        valid,
        computations,
        failed_index
    ) in results:

        validator = validators[
            validator_index
        ]

        total_computations += computations

        # Each checked hash is one validation computation.
        if validator.hash_validation_rate > 0:
            validator_time = (
                computations
                / validator.hash_validation_rate
            )
        else:
            validator_time = 0.0

        validator_times.append(
            validator_time
        )

        if valid:
            print(
                f"Node {validator_index + 1}: "
                f"{computations} steps checked, "
                f"VALID"
            )

        else:
            print(
                f"Node {validator_index + 1}: "
                f"hash validation FAILED at "
                f"step {failed_index}"
            )

            all_valid = False

    validation_time = (
        max(validator_times)
        if validator_times
        else 0.0
    )

    if all_valid:
        print(
            "[VALIDATOR] Hash chain is valid."
        )

    else:
        print(
            "[VALIDATOR] Hash chain is INVALID."
        )

    print(
        f"[VALIDATOR] Hash validation computations: "
        f"{total_computations}"
    )

    print(
        f"[VALIDATOR] Hash validation time: "
        f"{validation_time:.4f}s"
    )

    return (
        all_valid,
        total_computations,
        validation_time
    )

def _hash_slice_worker(args):

    (
        validator_index,
        steps,
        start_index,
        end_index,
        initial_hash
    ) = args

    previous_hash = initial_hash
    computations = 0

    for index in range(
        start_index,
        end_index
    ):

        # This validation attempt counts as one computation,
        # even if the step turns out to be invalid.
        computations += 1

        step = steps[index]

        expected_step_number = index + 1

        if step["step"] != expected_step_number:
            return (
                validator_index,
                False,
                computations,
                index
            )

        if step["previous_hash"] != previous_hash:
            return (
                validator_index,
                False,
                computations,
                index
            )

        hash_data = (
            previous_hash
            + str(step["step"])
            + str(step["data"])
        )

        expected_hash = utils.create_hash(
            hash_data
        )

        if step["hash"] != expected_hash:
            return (
                validator_index,
                False,
                computations,
                index
            )

        previous_hash = step["hash"]

    return (
        validator_index,
        True,
        computations,
        None
    )

def _parallel_path_validation(
    tsp,
    path,
    proposed_cost,
    transcript,
    validators
):
    """
    Validate the claimed path.

    Each edge in the proposed path is one path-validation
    computation.

    Validators operate in parallel.
    """

    if not path:
        print(
            "[VALIDATOR] Empty path."
        )
        return False, 0, 0.0

    if len(path) < 2:
        print(
            "[VALIDATOR] Path is too short."
        )
        return False, 0, 0.0

    if transcript is None:
        return False, 0, 0.0

    edge_count = len(path) - 1

    validators = validators[:min(
        len(validators),
        edge_count
    )]

    if not validators:
        return False, 0, 0.0

    num_validators = len(validators)

    # Split edges between validators.
    base_size = edge_count // num_validators
    remainder = edge_count % num_validators

    arguments = []

    current_index = 0

    for validator_index in range(
        num_validators
    ):

        slice_size = base_size

        if validator_index < remainder:
            slice_size += 1

        start_index = current_index
        end_index = (
            start_index + slice_size
        )

        arguments.append(
            (
                validator_index,
                tsp,
                path,
                transcript.path_index,
                start_index,
                end_index
            )
        )

        current_index = end_index

    with multiprocessing.Pool(
        processes=num_validators
    ) as pool:

        results = pool.map(
            _path_slice_worker,
            arguments
        )

    print(
        "\n[VALIDATOR] Path validation:"
    )

    all_valid = True
    total_computations = 0
    validator_times = []

    for (
        validator_index,
        valid,
        computations,
        calculated_cost,
        error
    ) in results:

        validator = validators[
            validator_index
        ]

        total_computations += computations

        if validator.path_validation_rate > 0:
            validator_time = (
                computations
                / validator.path_validation_rate
            )
        else:
            validator_time = 0.0

        validator_times.append(
            validator_time
        )

        if valid:

            print(
                f"Node {validator_index + 1}: "
                f"{computations} path checks, "
                f"VALID"
            )

        else:

            print(
                f"Node {validator_index + 1}: "
                f"PATH VALIDATION FAILED: "
                f"{error}"
            )

            all_valid = False

    calculated_cost = sum(
    result[3]
    for result in results
)

    if calculated_cost != proposed_cost:
        print(
            f"[VALIDATOR] Total cost mismatch: "
            f"calculated={calculated_cost}, "
            f"proposed={proposed_cost}"
        )
        all_valid = False
    else:
        print(
            f"[VALIDATOR] ✓ Total path cost = "
            f"{calculated_cost}"
        )

    validation_time = (
        max(validator_times)
        if validator_times
        else 0.0
    )

    if all_valid:

        print(
            "[VALIDATOR] Path validation successful."
        )

    else:

        print(
            "[VALIDATOR] Path validation failed."
        )

    print(
        f"[VALIDATOR] Path validation computations: "
        f"{total_computations}"
    )

    print(
        f"[VALIDATOR] Path validation time: "
        f"{validation_time:.4f}s"
    )

    return (
        all_valid,
        total_computations,
        validation_time
    )

def _path_slice_worker(args):

    (
        validator_index,
        tsp,
        path,
        path_index,
        start_index,
        end_index
    ) = args

    computations = 0
    calculated_cost = 0

    for i in range(
        start_index,
        end_index
    ):

        # One path/edge validation attempt.
        computations += 1

        source = path[i]
        destination = path[i + 1]

        expected_edge_cost = (
            tsp.matrix[source][destination]
        )

        if expected_edge_cost == utils.inf:
            return (
                validator_index,
                False,
                computations,
                calculated_cost,
                (
                    f"Edge {source} -> "
                    f"{destination} does not exist."
                )
            )

        calculated_cost += expected_edge_cost

        key = (
            tuple(path[:i + 1]),
            destination
        )

        data = path_index.get(key)

        if data is None:
            return (
                validator_index,
                False,
                computations,
                calculated_cost,
                (
                    f"Edge {source} -> "
                    f"{destination} was not found "
                    f"in transcript."
                )
            )

        if data["edge_cost"] != expected_edge_cost:
            return (
                validator_index,
                False,
                computations,
                calculated_cost,
                (
                    f"Edge cost mismatch for "
                    f"{source} -> {destination}."
                )
            )

        expected_child_path = (
            path[:i + 2]
        )

        if data["child_path"] != expected_child_path:
            return (
                validator_index,
                False,
                computations,
                calculated_cost,
                (
                    f"Child path mismatch for "
                    f"{source} -> {destination}."
                )
            )

    return (
        validator_index,
        True,
        computations,
        calculated_cost,
        None
    )

def _validate_calculated_path(
    tsp,
    path,
    proposed_cost,
    transcript
):
    total_cost = 0

    for i in range(len(path) - 1):

        source = path[i]
        destination = path[i + 1]

        expected_edge_cost = (
            tsp.matrix[source][destination]
        )

        if expected_edge_cost == utils.inf:
            return False

        total_cost += expected_edge_cost

        key = (
            tuple(path[:i + 1]),
            destination
        )

        data = transcript.path_index.get(key)

        if data is None:
            return False

        if data["edge_cost"] != expected_edge_cost:
            return False

        expected_child_path = path[:i + 2]

        if data["child_path"] != expected_child_path:
            return False

    if total_cost != proposed_cost:
        return False

    return True