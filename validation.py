from tspData import TspData
from tspFunctions import TspFunction
import multiprocessing
import utils


def council_validation(
    tsp: TspData,
    council,
    proposed_path,
    proposed_cost,
    initial_validations_per_second,
    branch_validation_nodes_per_second
):

    # --------------------------------------------------------
    # INITIAL VALIDATION
    # --------------------------------------------------------

    arguments = [
        (
            tsp,
            proposed_path,
            proposed_cost
        )
        for _ in council
    ]

    with multiprocessing.Pool() as pool:

        results = pool.map(
            _validate_node,
            arguments
        )

    # Each result is now simply True / False.
    initial_votes = sum(results)

    # Every council member performs exactly one complete
    # proposed-tour validation.
    initial_validations = len(council)

    if initial_validations == 0:
        return {
            "valid": False,
            "initial_validations": 0,
            "branch_validation_nodes": 0,
            "initial_compute_work": 0.0,
            "branch_compute_work": 0.0,
            "compute_work": 0.0,
            "validation_time": 0.0
        }

    # --------------------------------------------------------
    # INITIAL VALIDATION SIMULATED TIME
    # --------------------------------------------------------

    # All council members perform the initial validation
    # in parallel. Therefore the stage finishes when the
    # slowest validator completes its one validation.
    initial_validation_time = max(
        1.0 / node.initial_validation_rate
        for node in council
        if node.initial_validation_rate > 0
    )

    for index, node in enumerate(council):

        if node.initial_validation_rate <= 0:
            raise RuntimeError(
                "Council initial validation rate must be positive."
            )

        print(
            "INITIAL COUNCIL VALIDATOR",
            index,
            "| rate:",
            node.initial_validation_rate,
            "validations/s",
            "| simulated time:",
            1.0 / node.initial_validation_rate,
            "s"
        )

    print(
        "INITIAL COUNCIL TIME:",
        initial_validation_time,
        "s"
    )

    # --------------------------------------------------------
    # INITIAL VALIDATION REFERENCE COMPUTE WORK
    # --------------------------------------------------------

    # Unit:
    #
    # complete validations
    # --------------------
    # complete validations / second
    #
    # = reference-machine seconds
    initial_compute_work = (
        initial_validations
        / initial_validations_per_second
    )

    # --------------------------------------------------------
    # ULTIMATE / BRANCH VALIDATION
    # --------------------------------------------------------

    (
        ultimate_votes,
        ultimate_voters,
        branch_validation_nodes,
        ultimate_validation_time
    ) = _parallel_branch_validation(
        tsp,
        council,
        proposed_cost
    )

    # --------------------------------------------------------
    # BRANCH VALIDATION REFERENCE COMPUTE WORK
    # --------------------------------------------------------

    # Unit:
    #
    # examined B&B validation nodes
    # -----------------------------
    # examined B&B validation nodes / second
    #
    # = reference-machine seconds
    branch_compute_work = (
        branch_validation_nodes
        / branch_validation_nodes_per_second
    )

    # --------------------------------------------------------
    # TOTAL COUNCIL COMPUTATIONAL WORK
    # --------------------------------------------------------

    council_compute_work = (
        initial_compute_work
        + branch_compute_work
    )

    # --------------------------------------------------------
    # TOTAL SIMULATED VALIDATION TIME
    # --------------------------------------------------------

    # Initial validation and branch validation happen
    # sequentially, so their stage times are added.
    total_validation_time = (
        initial_validation_time
        + ultimate_validation_time
    )

    # --------------------------------------------------------
    # COUNCIL DECISION
    # --------------------------------------------------------

    total_votes = len(council)

    council_result = _council_voting(
        initial_votes,
        ultimate_votes,
        total_votes,
        ultimate_voters
    )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "valid": council_result,

        # Raw units
        "initial_validations":
            initial_validations,

        "branch_validation_nodes":
            branch_validation_nodes,

        # Normalized reference-machine work
        "initial_compute_work":
            initial_compute_work,

        "branch_compute_work":
            branch_compute_work,

        "compute_work":
            council_compute_work,

        # Simulated elapsed time
        "validation_time":
            total_validation_time
    }


def _validate_node(args):

    # Extract the validation arguments.
    tsp, proposed_path, proposed_cost = args

    # Assume the proposed solution is valid until
    # one of the validation checks fails.
    valid = True

    # --------------------------------------------------------
    # PATH STRUCTURE VALIDATION
    # --------------------------------------------------------

    # The path must exist.
    if not proposed_path:
        valid = False

    # The path must contain every city exactly once,
    # plus the repeated starting city at the end.
    elif len(proposed_path) != tsp.size + 1:
        valid = False

    # The tour must start and end at vertex 0.
    elif (
        proposed_path[0] != 0
        or proposed_path[-1] != 0
    ):
        valid = False

    # Every city index must be valid.
    elif any(
        vertex < 0 or vertex >= tsp.size
        for vertex in proposed_path[:-1]
    ):
        valid = False

    # Every city must appear exactly once before
    # returning to the starting city.
    elif len(set(proposed_path[:-1])) != tsp.size:
        valid = False

    # --------------------------------------------------------
    # PATH COST VALIDATION
    # --------------------------------------------------------

    else:

        total_cost = 0

        for i in range(len(proposed_path) - 1):

            source = proposed_path[i]
            destination = proposed_path[i + 1]

            edge_cost = tsp.matrix[source][destination]

            # The proposed path cannot contain a missing edge.
            if edge_cost == utils.inf:
                valid = False
                break

            total_cost += edge_cost

        # The independently calculated path cost must
        # match the claimed solution cost.
        if valid and total_cost != proposed_cost:
            valid = False

    return valid


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


def _parallel_branch_validation(
    tsp,
    council,
    proposed_cost
):

    branches = TspFunction.create_initial_branches(tsp)

    processes = []
    result_queue = multiprocessing.Queue()

    num_validators = len(council)

    branch_slices = [
        branches[i::num_validators]
        for i in range(num_validators)
    ]

    # --------------------------------------------------------
    # START VALIDATION PROCESSES
    # --------------------------------------------------------

    for node_index, branch_slice in enumerate(branch_slices):

        process = multiprocessing.Process(
            target=_branch_worker,
            args=(
                node_index,
                council[node_index].branch_validation_rate,
                tsp,
                branch_slice,
                result_queue,
                proposed_cost
            )
        )

        processes.append(process)
        process.start()

    # --------------------------------------------------------
    # WAIT FOR VALIDATORS
    # --------------------------------------------------------

    for process in processes:
        process.join()

    # --------------------------------------------------------
    # COLLECT RESULTS
    # --------------------------------------------------------

    results = []

    for _ in processes:
        results.append(
            result_queue.get()
        )

    ultimate_votes = 0
    ultimate_voters = 0

    # Raw number of B&B nodes examined during
    # branch validation.
    ultimate_computations = 0

    ultimate_validation_time = 0.0

    # --------------------------------------------------------
    # PROCESS RESULTS
    # --------------------------------------------------------

    for (
        node_index,
        valid,
        computations,
        branch_validation_rate
    ) in results:

        ultimate_computations += computations

        # A validator with no assigned B&B work does not vote.
        if computations == 0:
            continue

        if branch_validation_rate <= 0:
            raise RuntimeError(
                "Council branch validation rate must be positive."
            )

        # B&B validation nodes
        # --------------------
        # B&B validation nodes / second
        #
        # = simulated seconds
        node_validation_time = (
            computations
            / branch_validation_rate
        )

        print(
            "COUNCIL VALIDATOR",
            node_index,
            "| B&B nodes:",
            computations,
            "| rate:",
            branch_validation_rate,
            "nodes/s",
            "| simulated time:",
            node_validation_time,
            "s"
        )

        ultimate_validation_time = max(
            ultimate_validation_time,
            node_validation_time
        )

        ultimate_voters += 1

        if valid:
            ultimate_votes += 1

        print(
            "ULTIMATE COUNCIL TIME:",
            ultimate_validation_time,
            "s"
        )

    return (
        ultimate_votes,
        ultimate_voters,
        ultimate_computations,
        ultimate_validation_time
    )

def _branch_worker(
    node_index,
    branch_validation_rate,
    tsp,
    branches,
    result_queue,
    proposed_cost
):

    valid = True
    computations = 0

    # --------------------------------------------------------
    # VALIDATE ASSIGNED BRANCHES
    # --------------------------------------------------------

    for branch in branches:

        (
            branch_valid,
            branch_computations
        ) = TspFunction.validate_branch(
            tsp,
            branch,
            proposed_cost
        )

        # Raw number of B&B nodes examined.
        computations += branch_computations

        if not branch_valid:
            valid = False

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    result_queue.put(
        (
            node_index,
            valid,
            computations,
            branch_validation_rate
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
    validators,
    transcript_sigma,
    transcript_root
):

    print("Proof based validation")

    empty_result = {
        "valid": False,
        "hash_checks": 0,
        "semantic_checks": 0,
        "hash_time": 0.0,
        "semantic_time": 0.0,
        "validation_time": 0.0
    }

    if transcript is None:
        return empty_result

    if not validators:
        return empty_result

    # =========================================================
    # 1. HAMILTONIAN CYCLE
    # =========================================================

    if not _validate_hamiltonian_cycle(
        tsp,
        path
    ):

        return empty_result

    # =========================================================
    # 2. AUTHENTICATED ROOT
    # =========================================================

    if not _validate_transcript_root(
        tsp,
        transcript,
        transcript_sigma,
        transcript_root
    ):

        return empty_result

    # =========================================================
    # 3. HASH CHAIN
    # =========================================================

    (
        hash_valid,
        hash_checks,
        hash_time
    ) = _parallel_hash_validation(
        transcript,
        validators,
        transcript_root
    )

    if not hash_valid:

        result = empty_result.copy()

        result["hash_checks"] = (
            hash_checks
        )

        result["hash_time"] = (
            hash_time
        )

        result["validation_time"] = (
            hash_time
        )

        return result

    # =========================================================
    # 4. COMPLETE B&B REPLAY
    # =========================================================

    (
        semantic_valid,
        semantic_checks,
        reconstructed_path,
        reconstructed_cost
    ) = _validate_transcript_semantics(
        tsp,
        transcript,
        path,
        proposed_cost
    )

    if not semantic_valid:

        return {
            "valid": False,
            "hash_checks": hash_checks,
            "semantic_checks": semantic_checks,
            "hash_time": hash_time,
            "semantic_time": 0.0,
            "validation_time": hash_time
        }

    # ---------------------------------------------------------
    # Semantic replay is sequential because incumbent history
    # and the open frontier depend on preceding events.
    # ---------------------------------------------------------

    semantic_validator = validators[0]

    if (
        semantic_validator.semantic_validation_rate
        <= 0
    ):

        raise RuntimeError(
            "Proof semantic validation rate must be positive."
        )

    semantic_time = (
        semantic_checks
        / semantic_validator.semantic_validation_rate
    )

    total_time = (
        hash_time
        + semantic_time
    )

    return {
        "valid": True,
        "hash_checks": hash_checks,
        "semantic_checks": semantic_checks,
        "hash_time": hash_time,
        "semantic_time": semantic_time,
        "validation_time": total_time
    }

def _validate_transcript_semantics(
    tsp,
    transcript,
    proposed_path,
    proposed_cost
):

    print("Validating complete B&B transcript")

    if transcript is None:
        return False, 0, None, utils.inf

    computations = 0

    expected_incumbent = utils.inf
    expected_best_path = None

    # ---------------------------------------------------------
    # OPEN SEARCH FRONTIER
    #
    # Every node placed here MUST eventually be:
    #
    # - expanded
    # - pop-time pruned
    # - completed
    # - or identified as a dead end
    #
    # Otherwise the transcript is incomplete.
    # ---------------------------------------------------------

    open_nodes = {
        tuple(tsp.tsp_root.path):
            tsp.tsp_root
    }

    steps = transcript.steps
    index = 0

    def fail():
        return (
            False,
            computations,
            None,
            utils.inf
        )

    # =========================================================
    # PROCESS COMPLETE TRANSCRIPT
    # =========================================================

    while index < len(steps):

        data = steps[index]["data"]

        step_type = data.get("type")

        # -----------------------------------------------------
        # Determine which popped B&B node this transcript
        # record refers to.
        # -----------------------------------------------------

        if step_type == "branch":

            node_path = tuple(
                data["parent_path"]
            )

        elif step_type == "prune":

            node_path = tuple(
                data["path"]
            )

        elif step_type == "complete":

            node_path = tuple(
                data["parent_path"]
            )

        elif step_type == "dead_end":

            node_path = tuple(
                data["path"]
            )

        else:

            return fail()

        current_node = open_nodes.get(
            node_path
        )

        # The node must actually exist in the verifier's
        # independently reconstructed frontier.
        if current_node is None:

            return fail()

        # =====================================================
        # VERIFY B&B PRIORITY-QUEUE ORDER
        # =====================================================
        #
        # The real solver always pops a node having the
        # smallest lower bound currently present in the queue.
        #
        # Equal lower bounds may be processed in either order.

        minimum_lower_bound = min(
            node.cost
            for node in open_nodes.values()
        )

        if (
            current_node.cost
            != minimum_lower_bound
        ):

            return fail()

        # =====================================================
        # EXPANSION
        # =====================================================

        if step_type == "branch":

            # The solver would have pop-time pruned this node
            # before expansion.
            if (
                current_node.cost
                >= expected_incumbent
            ):

                return fail()

            # A complete node must be handled by the
            # complete/dead-end case instead.
            if (
                current_node.visited
                == tsp.size - 1
            ):

                return fail()

            # -------------------------------------------------
            # Independently determine EVERY legal child.
            # -------------------------------------------------

            expected_destinations = []

            for destination in range(
                current_node.size
            ):

                if (
                    current_node.matrix[
                        current_node.vertex
                    ][destination]
                    == utils.inf
                ):

                    continue

                if (
                    destination
                    in current_node.path
                ):

                    continue

                expected_destinations.append(
                    destination
                )

            # A node without children should have produced
            # a dead_end event.
            if not expected_destinations:

                return fail()

            # The parent is now being processed.
            del open_nodes[node_path]

            # -------------------------------------------------
            # Require EXACTLY one authenticated branch record
            # for EVERY legal child.
            #
            # The real solver iterates destinations in
            # ascending integer order, so we verify that order.
            # -------------------------------------------------

            for destination in expected_destinations:

                if index >= len(steps):

                    return fail()

                branch_data = (
                    steps[index]["data"]
                )

                computations += 1

                if (
                    branch_data.get("type")
                    != "branch"
                ):

                    return fail()

                if (
                    tuple(
                        branch_data[
                            "parent_path"
                        ]
                    )
                    != node_path
                ):

                    return fail()

                if (
                    branch_data[
                        "parent_vertex"
                    ]
                    != current_node.vertex
                ):

                    return fail()

                if (
                    branch_data[
                        "parent_lower_bound"
                    ]
                    != current_node.cost
                ):

                    return fail()

                if (
                    branch_data[
                        "selected_neighbour"
                    ]
                    != destination
                ):

                    return fail()

                # ---------------------------------------------
                # Reconstruct the B&B child independently.
                # ---------------------------------------------

                reduced_edge_cost = (
                    current_node.matrix[
                        current_node.vertex
                    ][destination]
                )

                expected_edge_cost = (
                    tsp.matrix[
                        current_node.vertex
                    ][destination]
                )

                if (
                    expected_edge_cost
                    == utils.inf
                ):

                    return fail()

                expected_child = (
                    TspFunction._create_child(
                        current_node,
                        tsp.matrix,
                        current_node.vertex,
                        destination
                    )
                )

                expected_reduction_cost = (
                    expected_child.cost
                    - current_node.cost
                    - reduced_edge_cost
                )

                # ---------------------------------------------
                # Verify every recorded value.
                # ---------------------------------------------

                if (
                    branch_data[
                        "child_path"
                    ]
                    != expected_child.path
                ):

                    return fail()

                if (
                    branch_data[
                        "edge_cost"
                    ]
                    != expected_edge_cost
                ):

                    return fail()

                if (
                    branch_data[
                        "reduction_cost"
                    ]
                    != expected_reduction_cost
                ):

                    return fail()

                if (
                    branch_data[
                        "child_lower_bound"
                    ]
                    != expected_child.cost
                ):

                    return fail()

                if (
                    branch_data[
                        "incumbent_cost"
                    ]
                    != expected_incumbent
                ):

                    return fail()

                expected_pruned = (
                    expected_child.cost
                    >= expected_incumbent
                )

                if (
                    branch_data["pruned"]
                    != expected_pruned
                ):

                    return fail()

                # ---------------------------------------------
                # Only unpruned children enter the verifier's
                # open frontier.
                # ---------------------------------------------

                if not expected_pruned:

                    child_key = tuple(
                        expected_child.path
                    )

                    if child_key in open_nodes:

                        return fail()

                    open_nodes[
                        child_key
                    ] = expected_child

                index += 1

            # We already advanced index through the complete
            # branch group.
            continue

        # =====================================================
        # POP-TIME PRUNE
        # =====================================================

        elif step_type == "prune":

            computations += 1

            if (
                data["vertex"]
                != current_node.vertex
            ):

                return fail()

            if (
                data["lower_bound"]
                != current_node.cost
            ):

                return fail()

            if (
                data["incumbent_cost"]
                != expected_incumbent
            ):

                return fail()

            # Exact solver pruning condition.
            if (
                current_node.cost
                < expected_incumbent
            ):

                return fail()

            del open_nodes[node_path]

            index += 1

        # =====================================================
        # COMPLETE TOUR
        # =====================================================

        elif step_type == "complete":

            computations += 1

            # Otherwise it would have been pop-time pruned.
            if (
                current_node.cost
                >= expected_incumbent
            ):

                return fail()

            if (
                current_node.visited
                != tsp.size - 1
            ):

                return fail()

            if (
                data["parent_vertex"]
                != current_node.vertex
            ):

                return fail()

            if (
                data["parent_lower_bound"]
                != current_node.cost
            ):

                return fail()

            if (
                data["selected_neighbour"]
                != 0
            ):

                return fail()

            final_edge = (
                tsp.matrix[
                    current_node.vertex
                ][0]
            )

            if final_edge == utils.inf:

                return fail()

            if (
                data["edge_cost"]
                != final_edge
            ):

                return fail()

            expected_path = (
                current_node.path
                + [0]
            )

            if (
                data["child_path"]
                != expected_path
            ):

                return fail()

            if (
                data["reduction_cost"]
                is not None
            ):

                return fail()

            if (
                data["child_lower_bound"]
                is not None
            ):

                return fail()

            if data["pruned"]:

                return fail()

            if (
                data["incumbent_cost"]
                != expected_incumbent
            ):

                return fail()

            completed_cost = (
                current_node.total_cost
                + final_edge
            )

            del open_nodes[node_path]

            # ---------------------------------------------
            # Independently reconstruct incumbent history.
            # ---------------------------------------------

            if (
                completed_cost
                < expected_incumbent
            ):

                expected_incumbent = (
                    completed_cost
                )

                expected_best_path = (
                    expected_path
                )

            index += 1

        # =====================================================
        # DEAD END
        # =====================================================

        elif step_type == "dead_end":

            computations += 1

            # Otherwise solver would have produced prune.
            if (
                current_node.cost
                >= expected_incumbent
            ):

                return fail()

            if (
                data["vertex"]
                != current_node.vertex
            ):

                return fail()

            if (
                data["lower_bound"]
                != current_node.cost
            ):

                return fail()

            if (
                data["incumbent_cost"]
                != expected_incumbent
            ):

                return fail()

            # ---------------------------------------------
            # Complete path but no return edge.
            # ---------------------------------------------

            if (
                current_node.visited
                == tsp.size - 1
            ):

                final_edge = (
                    tsp.matrix[
                        current_node.vertex
                    ][0]
                )

                if final_edge != utils.inf:

                    return fail()

                if (
                    data.get("reason")
                    != "no_return_edge"
                ):

                    return fail()

            # ---------------------------------------------
            # Non-complete node with no legal children.
            # ---------------------------------------------

            else:

                legal_children = []

                for destination in range(
                    current_node.size
                ):

                    if (
                        current_node.matrix[
                            current_node.vertex
                        ][destination]
                        == utils.inf
                    ):

                        continue

                    if (
                        destination
                        in current_node.path
                    ):

                        continue

                    legal_children.append(
                        destination
                    )

                if legal_children:

                    return fail()

                if (
                    data.get("reason")
                    != "no_children"
                ):

                    return fail()

            del open_nodes[node_path]

            index += 1

    # =========================================================
    # SEARCH COMPLETENESS
    # =========================================================

    # No generated B&B node may simply disappear from the
    # transcript.
    if open_nodes:

        print(
            "Proof failed: unprocessed B&B nodes:",
            list(open_nodes.keys())
        )

        return fail()

    # =========================================================
    # FINAL INCUMBENT MUST BE THE PROPOSED SOLUTION
    # =========================================================

    if expected_best_path is None:

        return fail()

    if (
        expected_incumbent
        != proposed_cost
    ):

        return fail()

    if (
        expected_best_path
        != proposed_path
    ):

        return fail()

    print(
        "Complete B&B replay valid."
    )

    print(
        "Reconstructed best path:",
        expected_best_path
    )

    print(
        "Reconstructed best cost:",
        expected_incumbent
    )

    return (
        True,
        computations,
        expected_best_path,
        expected_incumbent
    )

def _parallel_hash_validation(
    transcript,
    validators,
    transcript_root
):
    print("Parallel hash validation")

    #print("\n[HASH] Entering _parallel_hash_validation")

    # A transcript is required for hash-chain validation.
    if transcript is None:
        #print("[HASH FAIL] Transcript is None")
        return False, 0, 0.0

    steps = transcript.steps
    total_steps = len(steps)

    #print(f"[HASH] Total transcript steps: {total_steps}")
    #print(f"[HASH] Validators supplied: {len(validators)}")

    # An empty transcript cannot provide a valid proof.
    if total_steps == 0:
        #print("[HASH FAIL] Transcript contains no steps")
        return False, 0, 0.0

    # There is no benefit in creating more validation tasks
    # than there are transcript steps.
    validators = validators[:min(
        len(validators),
        total_steps
    )]

    num_validators = len(validators)

    initial_hash = transcript_root

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


        #print(
        #    f"[HASH] Validator {validator_index}: "
        #    f"steps {start_index} to {end_index - 1}"
        #)

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

    #print("[HASH] Starting multiprocessing workers")

    # ---------------------------------------------------------
    # Execute validation in parallel.
    # ---------------------------------------------------------

    #print("BEFORE HASH POOL", flush=True)

    # One worker process is created for each validator.
    
    with multiprocessing.Pool(
            processes=num_validators
        ) as pool:
    
            results = pool.map(
                _hash_slice_worker,
                arguments
            )

    """
    pool = multiprocessing.Pool(
        processes=num_validators
        )
        try:
            results = pool.map(
                _hash_slice_worker,
                arguments
            )
        finally:
            pool.close()
            pool.join()
        
    """
    """
        results = [
        _hash_slice_worker(argument)
        for argument in arguments
    ]
    """

    
    #print("AFTER HASH POOL", flush=True)

    #print("[HASH] Worker results:")

    #for result in results:
        #print(f"    {result}")

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

        #print(
        #    f"[HASH] Validator {validator_index}: "
        #    f"valid={valid}, "
        #    f"computations={computations}, "
        #    f"failed_index={failed_index}, "
        #    f"time={validator_time}"
        #)


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

    #print(
    #    f"[HASH] Final: valid={all_valid}, "
    #    f"computations={total_computations}, "
    #    f"time={validation_time}"
    #)

    return (
        all_valid,
        total_computations,
        validation_time
    )


def _hash_slice_worker(args):

    print("Hash slice worker")

    (
        validator_index,
        steps,
        start_index,
        end_index,
        initial_hash
    ) = args

    #print(
    #    f"[HASH WORKER {validator_index}] "
    #    f"Started: {start_index} -> {end_index - 1}"
    #)

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

        #if step["step"] != expected_step_number:
            #print(
            #    f"[HASH WORKER {validator_index} FAIL] "
            #    f"Step number mismatch at index {index}"
            #)
            #print(
            #    f"Expected: {expected_step_number}, "
            #    f"got: {step['step']}"
            #)

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
        #if step["previous_hash"] != previous_hash:
            #print(
        #        f"[HASH WORKER {validator_index} FAIL] "
        #        f"Previous hash mismatch at index {index}"
        #    )
            #print(f"Expected: {previous_hash}")
            #print(f"Stored:   {step['previous_hash']}")

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

        #if step["hash"] != expected_hash:
        #    #print(
        #        f"[HASH WORKER {validator_index} FAIL] "
        #        f"Current hash mismatch at index {index}"
        #    )
            #print(f"Expected: {expected_hash}")
            #print(f"Stored:   {step['hash']}")
            #print(f"Data:     {step['data']}")

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

    #print(
    #    f"[HASH WORKER {validator_index}] "
    #    f"Passed {computations} checks"
    #)

    # All assigned transcript steps passed validation.
    return (
        validator_index,
        True,
        computations,
        None
    )

def _validate_hamiltonian_cycle(tsp, path):

    print("Validating hamiltonian cycle")
    # A path must exist.
    if not path:
        return False

    # A Hamiltonian cycle over n cities contains n + 1 vertices
    # because the starting city is repeated at the end.
    if len(path) != tsp.size + 1:
        return False

    # The implemented TSP search always starts and ends at city 0.
    if path[0] != 0 or path[-1] != 0:
        return False

    # Every city before the final repeated 0 must be a valid city.
    if any(
        vertex < 0 or vertex >= tsp.size
        for vertex in path[:-1]
    ):
        return False

    # Every city must occur exactly once before returning to city 0.
    if len(set(path[:-1])) != tsp.size:
        return False

    return True

def _validate_transcript_root(
    tsp,
    transcript,
    transcript_sigma,
    transcript_root
):

    print("Validating transcript root")

    # The transcript must contain an authenticated root.
    if not hasattr(transcript, "root"):
        return False

    root = tsp.tsp_root

    expected_children = []

    # Independently reconstruct every legal first-level child.
    for neighbour in range(root.size):

        if (
            root.matrix[
                root.vertex
            ][neighbour] == utils.inf
        ):
            continue

        if neighbour in root.path:
            continue

        child = TspFunction._create_child(
            root,
            tsp.matrix,
            root.vertex,
            neighbour
        )

        edge_cost = tsp.matrix[
            root.vertex
        ][neighbour]

        reduced_edge_cost = root.matrix[
            root.vertex
        ][neighbour]

        reduction_cost = (
            child.cost
            - root.cost
            - reduced_edge_cost
        )

        expected_children.append({
            "selected_neighbour": neighbour,
            "child_path": child.path[:],
            "edge_cost": edge_cost,
            "reduction_cost": reduction_cost,
            "child_lower_bound": child.cost
        })

    # Reconstruct exactly the same root data MainFunctions
    # generated before mining began.
    expected_root_data = {
        "path": root.path[:],
        "vertex": root.vertex,
        "visited": root.visited,
        "lower_bound": root.cost,
        "children": expected_children
    }

    # Transcript must contain the correct root data.
    if (
        transcript.root["data"]
        != expected_root_data
    ):
        return False

    # Root must really be step 0.
    if transcript.root["step"] != 0:
        return False

    if transcript.root["previous_hash"] is not None:
        return False

    # Independently reconstruct the root hash.
    calculated_root_hash = utils.create_hash(
        transcript_sigma.hex()
        + str(expected_root_data)
        + str(tsp.matrix)
    )

    # It must equal the root that MainFunctions created
    # before mining started.
    if calculated_root_hash != transcript_root:
        return False

    # The transcript must also contain that exact root.
    if (
        transcript.root["hash"]
        != transcript_root
    ):
        return False

    return True