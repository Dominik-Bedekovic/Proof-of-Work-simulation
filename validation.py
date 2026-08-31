from tspData import TspData
from tspFunctions import TspFunction
import multiprocessing
import utils


def council_validation(
    tsp: TspData,
    council,
    proposed_path,
    proposed_cost
):

    # --------------------------------------------------------
    # INITIAL VALIDATION
    # --------------------------------------------------------

    # Prepare the same validation arguments for every council
    # member. Each tuple contains the TSP data, proposed path,
    # and proposed cost.
    arguments = [
        (tsp, proposed_path, proposed_cost)
        for _ in council
    ]

    # Create a multiprocessing pool so that every council
    # member can independently validate the proposed solution
    # in parallel.
    with multiprocessing.Pool() as pool:

        # Execute _validate_node for every council member.
        # The returned result for each member contains:
        # (whether the solution is valid, number of computations)
        results = pool.map(
            _validate_node,
            arguments
        )

    # Count the number of council members that initially
    # considered the proposed solution valid.
    initial_votes = sum(
        valid
        for valid, computations in results
    )

    # Count all computations performed during the initial
    # validation stage.
    initial_computations = sum(
        computations
        for valid, computations in results
    )

    # Calculate the time required for the initial validation.
    #
    # Since the validators work in parallel, the stage finishes
    # when the slowest validator finishes. Therefore, the
    # maximum validation time is used.
    initial_validation_time = max(
        computations / node.validation_rate
        for node, (_, computations)
        in zip(council, results)
    )

    # --------------------------------------------------------
    # ULTIMATE VALIDATION
    # --------------------------------------------------------

    # Perform the more computationally expensive Branch and
    # Bound validation. The search branches are distributed
    # between the council members and processed in parallel.
    (
        ultimate_votes,
        ultimate_voters,
        ultimate_computations,
        ultimate_validation_time
    ) = _parallel_branch_validation(
        tsp,
        council,
        proposed_cost
    )

    # --------------------------------------------------------
    # COMBINE VALIDATION RESULTS
    # --------------------------------------------------------

    # The total number of council members participating in the
    # initial validation.
    total_votes = len(council)

    # Combine the computational work from both validation stages.
    total_computations = (
        initial_computations
        + ultimate_computations
    )

    # Combine the elapsed time of both validation stages.
    #
    # The two stages are performed sequentially, so their times
    # are added together.
    total_validation_time = (
        initial_validation_time
        + ultimate_validation_time
    )

    # --------------------------------------------------------
    # COUNCIL DECISION
    # --------------------------------------------------------

    # Determine whether the validation results satisfy the
    # council's voting rules.
    council_result = _council_voting(
        initial_votes,
        ultimate_votes,
        total_votes,
        ultimate_voters
    )

    # Return the final decision together with the computational
    # work and time required for validation.
    return (
        council_result,
        total_computations,
        total_validation_time
    )


def _validate_node(args):

    # Extract the validation arguments.
    tsp, proposed_path, proposed_cost = args

    # Initialize the computation counter.
    computations = 0

    # Assume the proposed solution is valid until a validation
    # condition fails.
    valid = True

    # Count the initial validation operation.
    computations += 1

    # --------------------------------------------------------
    # PATH STRUCTURE VALIDATION
    # --------------------------------------------------------

    # The tour must start and end at vertex 0.
    if (
        proposed_path[0] != 0
        or proposed_path[-1] != 0
    ):
        valid = False

    # The path must contain one additional vertex because
    # the starting vertex 0 is repeated at the end.
    elif len(proposed_path) != tsp.size + 1:
        valid = False

    elif any(
    vertex < 0 or vertex >= tsp.size
    for vertex in proposed_path[:-1]
    ):
        valid = False

    # Remove the final repeated starting vertex and check that
    # the remaining vertices are all unique.
    elif len(set(proposed_path[:-1])) != tsp.size:
        valid = False

    # --------------------------------------------------------
    # PATH COST VALIDATION
    # --------------------------------------------------------

    else:

        # Initialize the calculated total path cost.
        total_cost = 0

        # Visit every edge in the proposed path.
        for i in range(len(proposed_path) - 1):

            # Get the source and destination vertices.
            source = proposed_path[i]
            destination = proposed_path[i + 1]

            # Retrieve the cost of the corresponding edge.
            edge_cost = tsp.matrix[source][destination]

            # Count the edge validation as a computation.
            computations += 1

            # If the edge does not exist, the proposed path
            # is invalid.
            if edge_cost == utils.inf:
                valid = False
                break

            # Add the edge cost to the calculated total.
            total_cost += edge_cost

        # The calculated cost must match the cost claimed by
        # the node that proposed the solution.
        if total_cost != proposed_cost:
            valid = False

    # Return the validation result and computational work.
    return (
        valid,
        computations
    )


def _parallel_branch_validation(
    tsp,
    council,
    proposed_cost
):
    # Generate the initial Branch and Bound search branches.
    branches = TspFunction.create_initial_branches(tsp)

    # Store the multiprocessing.Process objects so they can
    # later be waited on with join().
    processes = []

    # Create a multiprocessing queue through which worker
    # processes return their results to the main process.
    result_queue = multiprocessing.Queue()

    # Determine how many validators are available.
    num_validators = len(council)

    # --------------------------------------------------------
    # DIVIDE BRANCHES BETWEEN VALIDATORS
    # --------------------------------------------------------

    # Distribute the branches between validators.
    #
    # For example, with three validators:
    #
    # validator 1 -> branches 0, 3, 6, ...
    # validator 2 -> branches 1, 4, 7, ...
    # validator 3 -> branches 2, 5, 8, ...
    branch_slices = [
        branches[i::num_validators]
        for i in range(num_validators)
    ]

    # --------------------------------------------------------
    # START VALIDATION PROCESSES
    # --------------------------------------------------------

    for node_index, branch_slice in enumerate(branch_slices):

        # Create a separate process for this validator.
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

        # Store the process so it can later be joined.
        processes.append(process)

        # Start the validator process.
        process.start()

    # --------------------------------------------------------
    # WAIT FOR ALL VALIDATORS
    # --------------------------------------------------------

    # Wait until every validator process has finished.
    for process in processes:
        process.join()

    # --------------------------------------------------------
    # COLLECT VALIDATION RESULTS
    # --------------------------------------------------------

    results = []

    # Retrieve every result placed into the queue by the
    # validator processes.
    for _ in processes:
        results.append(
            result_queue.get()
        )

    # Initialize the ultimate validation statistics.
    ultimate_votes = 0
    ultimate_voters = 0
    ultimate_computations = 0
    ultimate_validation_time = 0

    # --------------------------------------------------------
    # PROCESS VALIDATOR RESULTS
    # --------------------------------------------------------

    for (
        node_index,
        valid,
        computations,
        validation_rate
    ) in results:

        # Add this validator's computations to the total.
        ultimate_computations += computations

        # A validator that received no branches performed no
        # validation work and therefore does not participate
        # in the ultimate vote.
        if computations == 0:
            continue

        # Calculate the simulated time required by this
        # validator based on its validation rate.
        node_validation_time = (
            computations / validation_rate
        )

        # Since validators work in parallel, the ultimate
        # validation stage finishes when the slowest validator
        # finishes.
        ultimate_validation_time = max(
            ultimate_validation_time,
            node_validation_time
        )

        # Count this validator as an active voter.
        ultimate_voters += 1

        # If all assigned branches were valid, this validator
        # casts a positive vote.
        if valid:
            ultimate_votes += 1

    # Return the results of the ultimate validation stage.
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

    # Assume all assigned branches are valid.
    valid = True

    # Initialize the computation counter.
    computations = 0

    # --------------------------------------------------------
    # VALIDATE ASSIGNED BRANCHES
    # --------------------------------------------------------

    for branch in branches:

        # Validate the current branch against the proposed cost.
        (
            branch_valid,
            branch_computations
        ) = TspFunction.validate_branch(
            tsp,
            branch,
            proposed_cost
        )

        # Add the branch's computational work to this
        # validator's total.
        computations += branch_computations

        # If any assigned branch is invalid, the validator
        # rejects its assigned portion of the search space.
        if not branch_valid:
            valid = False

    # --------------------------------------------------------
    # RETURN RESULT TO MAIN PROCESS
    # --------------------------------------------------------

    # Send the validator's result back to the main process.
    result_queue.put(
        (
            node_index,
            valid,
            computations,
            validation_rate
        )
    )


def _council_voting(
    initial_votes,
    ultimate_votes,
    total_votes,
    ultimate_voters
):
    # The council cannot accept the solution if no validator
    # participated in the ultimate validation stage.
    if ultimate_voters == 0:
        return False

    # Both validation stages require unanimous approval.
    if initial_votes == total_votes and ultimate_votes == ultimate_voters:
        return True

    return False

def proof_based_validation(
    tsp,
    path,
    proposed_cost,
    transcript,
    validators
):

    # A transcript is required because it contains the recorded
    # proof of how the proposed PoUW solution was generated.
    if transcript is None:
        return False, 0, 0.0

    # At least one validator is required to perform validation.
    if not validators:
        return False, 0, 0.0

    # =========================================================
    # 1. TRANSCRIPT HASH-CHAIN VALIDATION
    # =========================================================

    # The transcript is divided between the available validators.
    # Each validator independently verifies its assigned section
    # of the hash chain.
    (
        hash_valid,
        hash_computations,
        hash_time
    ) = _parallel_hash_validation(
        transcript,
        validators
    )

    # If any part of the hash chain is invalid, the transcript
    # cannot be trusted and the proposed solution is rejected.
    if not hash_valid:
        return False, hash_computations, hash_time

    # =========================================================
    # 2. TSP PATH VALIDATION
    # =========================================================

    # The proposed path is divided between the validators.
    # Each validator checks its assigned edges against the TSP
    # matrix and the corresponding transcript entries.
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

    # If the proposed path is invalid, reject the solution.
    if not path_valid:
        return (
            False,
            hash_computations + path_computations,
            hash_time + path_time
        )

    # Both validation stages were completed successfully.
    total_computations = (
        hash_computations
        + path_computations
    )

    total_time = (
        hash_time
        + path_time
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

    # A transcript is required for hash-chain validation.
    if transcript is None:
        return False, 0, 0.0

    steps = transcript.steps
    total_steps = len(steps)

    # An empty transcript cannot provide a valid proof.
    if total_steps == 0:
        return False, 0, 0.0

    # There is no benefit in creating more validation tasks
    # than there are transcript steps.
    validators = validators[:min(
        len(validators),
        total_steps
    )]

    num_validators = len(validators)

    # Calculate the initial hash from the value from which
    # the transcript hash chain was originally constructed.
    initial_hash = utils.create_hash(
        transcript.sigma
    )

    arguments = []

    # ---------------------------------------------------------
    # Divide transcript steps between validators.
    # ---------------------------------------------------------

    # Each validator receives approximately the same number
    # of transcript steps.
    base_size = (
        total_steps // num_validators
    )

    # Remaining steps are distributed one by one to the
    # first validators.
    remainder = (
        total_steps % num_validators
    )

    current_index = 0

    for validator_index in range(num_validators):

        slice_size = base_size

        # Distribute the remaining transcript steps evenly.
        if validator_index < remainder:
            slice_size += 1

        start_index = current_index
        end_index = (
            start_index + slice_size
        )

        # The first validator starts from hash(sigma).
        if start_index == 0:
            slice_initial_hash = initial_hash

        # Every other validator starts from the hash stored
        # by the transcript step immediately before its section.
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

    # ---------------------------------------------------------
    # Execute validation in parallel.
    # ---------------------------------------------------------

    # One worker process is created for each validator.
    with multiprocessing.Pool(
        processes=num_validators
    ) as pool:

        results = pool.map(
            _hash_slice_worker,
            arguments
        )

    all_valid = True
    total_computations = 0
    validator_times = []

    # ---------------------------------------------------------
    # Process validator results.
    # ---------------------------------------------------------

    for (
        validator_index,
        valid,
        computations,
        failed_index
    ) in results:

        validator = validators[
            validator_index
        ]

        # Add the number of hash checks performed by this validator.
        total_computations += computations

        # Convert the number of performed checks into the
        # simulated validation time of this validator.
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

        # A single invalid transcript section is sufficient
        # to reject the entire proof.
        if not valid:
            all_valid = False

    # Validators operate simultaneously, so elapsed validation
    # time is determined by the slowest validator.
    validation_time = (
        max(validator_times)
        if validator_times
        else 0.0
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

    # Start from the hash that precedes this validator's section.
    previous_hash = initial_hash
    computations = 0

    # Validate every transcript step assigned to this validator.
    for index in range(
        start_index,
        end_index
    ):

        # Each transcript step requires one hash-chain validation.
        computations += 1

        step = steps[index]

        # -----------------------------------------------------
        # Verify the transcript step number.
        # -----------------------------------------------------

        expected_step_number = index + 1

        if step["step"] != expected_step_number:
            return (
                validator_index,
                False,
                computations,
                index
            )

        # -----------------------------------------------------
        # Verify the previous hash.
        # -----------------------------------------------------

        # The stored previous hash must match the hash generated
        # by the preceding transcript step.
        if step["previous_hash"] != previous_hash:
            return (
                validator_index,
                False,
                computations,
                index
            )

        # -----------------------------------------------------
        # Recalculate the current hash.
        # -----------------------------------------------------

        # Reconstruct exactly the same data that was used when
        # the transcript entry was originally created.
        hash_data = (
            previous_hash
            + str(step["step"])
            + str(step["data"])
        )

        expected_hash = utils.create_hash(
            hash_data
        )

        # The recalculated hash must match the stored hash.
        if step["hash"] != expected_hash:
            return (
                validator_index,
                False,
                computations,
                index
            )

        # The current hash becomes the previous hash for the
        # next transcript step in this validator's section.
        previous_hash = step["hash"]

    # All assigned transcript steps passed validation.
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

    # A path is required for validation.
    if not path:
        return False, 0, 0.0

    # A path containing fewer than two vertices has no edge to validate.
    if len(path) < 2:
        return False, 0, 0.0

    # The transcript is required because the path must also be
    # compared against the recorded proof.
    if transcript is None:
        return False, 0, 0.0

    edge_count = len(path) - 1

    # There is no reason to create more validators than there
    # are edges to validate.
    validators = validators[:min(
        len(validators),
        edge_count
    )]

    if not validators:
        return False, 0, 0.0

    num_validators = len(validators)

    # =========================================================
    # Divide path between validators.
    # =========================================================

    base_size = (
        edge_count // num_validators
    )

    remainder = (
        edge_count % num_validators
    )

    arguments = []
    current_index = 0

    for validator_index in range(
        num_validators
    ):

        slice_size = base_size

        # Distribute remaining edges among the first validators.
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

    # =========================================================
    # Execute path validation in parallel.
    # =========================================================

    with multiprocessing.Pool(
        processes=num_validators
    ) as pool:

        results = pool.map(
            _path_slice_worker,
            arguments
        )

    all_valid = True
    total_computations = 0
    validator_times = []

    # =========================================================
    # Process validator results.
    # =========================================================

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

        # Count all edge validations performed by the validators.
        total_computations += computations

        # Convert validation computations into simulated time.
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

        # If one validator detects an invalid edge or transcript
        # entry, the proposed path is rejected.
        if not valid:
            all_valid = False

    # Sum the independently calculated costs of all path sections.
    calculated_cost = sum(
        result[3]
        for result in results
    )

    # The independently calculated total must match the cost
    # claimed by the PoUW miner.
    if calculated_cost != proposed_cost:
        all_valid = False

    # Because validators operate in parallel, elapsed validation
    # time is determined by the slowest validator.
    validation_time = (
        max(validator_times)
        if validator_times
        else 0.0
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

    # Validate every edge assigned to this validator.
    for i in range(
        start_index,
        end_index
    ):

        # One edge validation represents one validation computation.
        computations += 1

        source = path[i]
        destination = path[i + 1]

        # =====================================================
        # Verify that the edge exists.
        # =====================================================

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

        # Add the independently verified edge cost to the
        # validator's partial path cost.
        calculated_cost += expected_edge_cost

        # =====================================================
        # Find the corresponding transcript entry.
        # =====================================================

        # The key identifies the path prefix and the newly
        # selected destination.
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

        # =====================================================
        # Verify the recorded edge cost.
        # =====================================================

        # The transcript must contain the same edge cost
        # as the original TSP matrix.
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

        # =====================================================
        # Verify the recorded child path.
        # =====================================================

        # Reconstruct the path that should have been recorded
        # after adding the destination city.
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

    # Every assigned edge passed validation.
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

    # Check every edge in the proposed path.
    for i in range(len(path) - 1):

        source = path[i]
        destination = path[i + 1]

        # Retrieve the expected edge cost from the TSP matrix.
        expected_edge_cost = (
            tsp.matrix[source][destination]
        )

        # The edge must exist in the graph.
        if expected_edge_cost == utils.inf:
            return False

        total_cost += expected_edge_cost

        # Find the corresponding edge in the transcript.
        key = (
            tuple(path[:i + 1]),
            destination
        )

        data = transcript.path_index.get(key)

        if data is None:
            return False

        # Verify that the transcript recorded the same edge cost
        # as the original TSP matrix.
        if data["edge_cost"] != expected_edge_cost:
            return False

        # Verify that the transcript recorded the correct path
        # after adding the destination city.
        expected_child_path = path[:i + 2]

        if data["child_path"] != expected_child_path:
            return False

    # Finally, compare the independently calculated path cost
    # with the cost claimed by the PoUW miner.
    if total_cost != proposed_cost:
        return False

    return True

