"""Check proposed tours through council search or complete B&B transcript replay."""

from tspData import TspData
from tspFunctions import TspFunction
from hostRuntime import host_map, check_cancelled
import utils
import math
from numbers import Real


def council_validation(
    tsp: TspData,
    council,
    proposed_path,
    proposed_cost,
    initial_validations_per_second,
    branch_validation_nodes_per_second,
    host_workers=1,
):
    """Check the tour and partition the search across validators; require unanimous
    approval.
    """

    # Each council member first checks the complete submitted tour.
    arguments = [(tsp, proposed_path, proposed_cost) for _ in council]
    results = host_map(_validate_node, arguments, host_workers)
    initial_votes = sum(results)
    initial_validations = len(council)
    if initial_validations == 0:
        return {
            "valid": False,
            "initial_validations": 0,
            "branch_validation_nodes": 0,
            "initial_compute_work": 0.0,
            "branch_compute_work": 0.0,
            "compute_work": 0.0,
            "validation_time": 0.0,
        }

    # These checks run in parallel, so the slowest validator sets elapsed time.
    initial_validation_time = max(
        (
            1.0 / node.initial_validation_rate
            for node in council
            if node.initial_validation_rate > 0
        )
    )
    for index, node in enumerate(council):
        if node.initial_validation_rate <= 0:
            raise RuntimeError("Council initial validation rate must be positive.")
    initial_compute_work = initial_validations / initial_validations_per_second
    (
        ultimate_votes,
        ultimate_voters,
        branch_validation_nodes,
        ultimate_validation_time,
    ) = _parallel_branch_validation(tsp, council, proposed_cost, host_workers)
    branch_compute_work = branch_validation_nodes / branch_validation_nodes_per_second
    council_compute_work = initial_compute_work + branch_compute_work
    total_validation_time = initial_validation_time + ultimate_validation_time
    total_votes = len(council)
    council_result = _council_voting(
        initial_votes, ultimate_votes, total_votes, ultimate_voters
    )
    return {
        "valid": council_result,
        "initial_validations": initial_validations,
        "branch_validation_nodes": branch_validation_nodes,
        "initial_compute_work": initial_compute_work,
        "branch_compute_work": branch_compute_work,
        "compute_work": council_compute_work,
        "validation_time": total_validation_time,
    }


def _validate_node(args):
    """Adapt one proposed tour to the argument tuple expected by multiprocessing."""
    tsp, proposed_path, proposed_cost = args
    return _validate_proposed_tour(tsp, proposed_path, proposed_cost)


def _parallel_branch_validation(tsp, council, proposed_cost, host_workers=1):
    """Assign disjoint initial branches and aggregate votes, node counts, and slowest
    time.
    """
    branches = TspFunction.create_initial_branches(tsp)
    num_validators = len(council)
    if not num_validators:
        return (0, 0, 0, 0.0)

    # Branches are disjoint, not replicated votes on the same search work.
    branch_slices = [branches[i::num_validators] for i in range(num_validators)]
    arguments = [
        (index, council[index].branch_validation_rate, tsp, branches, proposed_cost)
        for index, branches in enumerate(branch_slices)
    ]
    results = host_map(_branch_worker, arguments, host_workers)
    ultimate_votes = 0
    ultimate_voters = 0
    ultimate_computations = 0
    ultimate_validation_time = 0.0
    for node_index, valid, computations, branch_validation_rate in results:
        ultimate_computations += computations

        # An unassigned worker contributes neither a vote nor branch-processing time.
        if computations == 0:
            continue
        if branch_validation_rate <= 0:
            raise RuntimeError("Council branch validation rate must be positive.")
        node_validation_time = computations / branch_validation_rate
        ultimate_validation_time = max(ultimate_validation_time, node_validation_time)
        ultimate_voters += 1
        if valid:
            ultimate_votes += 1
    return (
        ultimate_votes,
        ultimate_voters,
        ultimate_computations,
        ultimate_validation_time,
    )


def _branch_worker(args):
    """Return one logical validator's result; worker exceptions propagate to the caller."""
    node_index, branch_validation_rate, tsp, branches, proposed_cost = args
    valid = True
    computations = 0
    for branch in branches:
        check_cancelled()
        branch_valid, branch_computations = TspFunction.validate_branch(
            tsp, branch, proposed_cost
        )
        computations += branch_computations
        if not branch_valid:
            valid = False
    return (node_index, valid, computations, branch_validation_rate)


def _council_voting(initial_votes, ultimate_votes, total_votes, ultimate_voters):
    """Approve only when every participating validator approves both required stages."""
    if ultimate_voters == 0:
        return False

    # Any branch finding a cheaper tour must be able to reject the proposal.
    if initial_votes == total_votes and ultimate_votes == ultimate_voters:
        return True
    return False


def proof_based_validation(
    tsp, path, proposed_cost, transcript, validators, transcript_sigma, transcript_root,
    host_workers=1,
):
    """Validate the submitted cost and full certificate; return decision, counts, and
    modeled times.
    """
    empty_result = {
        "valid": False,
        "hash_checks": 0,
        "semantic_checks": 0,
        "hash_time": 0.0,
        "semantic_time": 0.0,
        "validation_time": 0.0,
    }
    if transcript is None:
        return empty_result
    if not validators:
        return empty_result
    semantic_setup_checks = 0

    # Validate the submitted path's actual edge sum, not just the transcript's cost.
    if not _validate_proposed_tour(tsp, path, proposed_cost):
        return empty_result
    semantic_setup_checks += 1
    if not _validate_transcript_root(
        tsp, transcript, transcript_sigma, transcript_root
    ):
        return empty_result
    root_children = transcript.root["data"].get("children", [])

    # These composite setup units match the semantic benchmark's counting rule.
    semantic_setup_checks += 1 + len(root_children)
    hash_valid, hash_checks, hash_time = _parallel_hash_validation(
        transcript, validators, transcript_root, host_workers
    )
    if not hash_valid:
        result = empty_result.copy()
        result["hash_checks"] = hash_checks
        result["hash_time"] = hash_time
        result["validation_time"] = hash_time
        return result
    semantic_valid, replay_checks, reconstructed_path, reconstructed_cost = (
        _validate_transcript_semantics(tsp, transcript, path, proposed_cost)
    )
    semantic_checks = semantic_setup_checks + replay_checks

    # Hash slices are parallel, but complete semantic replay uses one validator.
    semantic_validator = validators[0]
    if semantic_validator.semantic_validation_rate <= 0:
        raise RuntimeError("Proof semantic validation rate must be positive.")
    semantic_time = semantic_checks / semantic_validator.semantic_validation_rate
    if not semantic_valid:
        return {
            "valid": False,
            "hash_checks": hash_checks,
            "semantic_checks": semantic_checks,
            "hash_time": hash_time,
            "semantic_time": semantic_time,
            "validation_time": hash_time + semantic_time,
        }
    total_time = hash_time + semantic_time
    return {
        "valid": True,
        "hash_checks": hash_checks,
        "semantic_checks": semantic_checks,
        "hash_time": hash_time,
        "semantic_time": semantic_time,
        "validation_time": total_time,
    }


# The optional compatibility argument is retained for older callers; validation is silent.
def _validate_transcript_semantics(
    tsp, transcript, proposed_path, proposed_cost, debug=True
):
    """Reconstruct every generated node, pruning decision, and incumbent until the
    frontier is empty.

    Completion order may differ from dispatch priority. This checks the search
    result, not worker timing or physical work. Equivalent optimum tours are
    permitted.
    """
    if transcript is None:
        return (False, 0, None, utils.inf)
    if not _validate_proposed_tour(tsp, proposed_path, proposed_cost):
        return (False, 0, None, utils.inf)
    computations = 0
    expected_incumbent = utils.inf
    expected_best_path = None

    # Every generated, unpruned node must eventually be accounted for.
    open_nodes = {tuple(tsp.tsp_root.path): tsp.tsp_root}
    steps = transcript.steps
    index = 0

    def fail():
        """Return a failed replay result with the number of semantic records checked so
        far.
        """
        return (False, computations, None, utils.inf)

    while index < len(steps):
        check_cancelled()
        data = steps[index]["data"]
        step_type = data.get("type")
        if step_type == "branch":
            node_path = tuple(data["parent_path"])
        elif step_type == "prune":
            node_path = tuple(data["path"])
        elif step_type == "complete":
            node_path = tuple(data["parent_path"])
        elif step_type == "dead_end":
            node_path = tuple(data["path"])
        else:
            return fail()

        # Parallel completion need not follow minimum-bound order. The node must
        # still belong to the independently reconstructed frontier.
        current_node = open_nodes.get(node_path)
        if current_node is None:
            return fail()
        if step_type == "branch":
            if current_node.cost >= expected_incumbent:
                return fail()
            if current_node.visited == tsp.size - 1:
                return fail()

            # Recompute every legal child so omitted branches cannot hide a better tour.
            expected_destinations = []
            for destination in range(current_node.size):
                if current_node.matrix[current_node.vertex][destination] == utils.inf:
                    continue
                if destination in current_node.path:
                    continue
                expected_destinations.append(destination)
            if not expected_destinations:
                return fail()
            del open_nodes[node_path]

            # Require exactly one record per legal child in the solver's neighbor order.
            for destination in expected_destinations:
                if index >= len(steps):
                    return fail()
                branch_data = steps[index]["data"]
                computations += 1
                if branch_data.get("type") != "branch":
                    return fail()
                if tuple(branch_data["parent_path"]) != node_path:
                    return fail()
                if branch_data["parent_vertex"] != current_node.vertex:
                    return fail()
                if branch_data["parent_lower_bound"] != current_node.cost:
                    return fail()
                if branch_data["selected_neighbour"] != destination:
                    return fail()
                reduced_edge_cost = current_node.matrix[current_node.vertex][
                    destination
                ]
                expected_edge_cost = tsp.matrix[current_node.vertex][destination]
                if expected_edge_cost == utils.inf:
                    return fail()
                expected_child = TspFunction._create_child(
                    current_node, tsp.matrix, current_node.vertex, destination
                )
                expected_reduction_cost = (
                    expected_child.cost - current_node.cost - reduced_edge_cost
                )
                if branch_data["child_path"] != expected_child.path:
                    return fail()
                if branch_data["edge_cost"] != expected_edge_cost:
                    return fail()
                if branch_data["reduction_cost"] != expected_reduction_cost:
                    return fail()
                if branch_data["child_lower_bound"] != expected_child.cost:
                    return fail()
                if branch_data["incumbent_cost"] != expected_incumbent:
                    return fail()
                expected_pruned = expected_child.cost >= expected_incumbent
                if branch_data["pruned"] != expected_pruned:
                    return fail()
                if not expected_pruned:
                    child_key = tuple(expected_child.path)
                    if child_key in open_nodes:
                        return fail()
                    open_nodes[child_key] = expected_child
                index += 1
            continue
        elif step_type == "prune":
            computations += 1
            if data["vertex"] != current_node.vertex:
                return fail()
            if data["lower_bound"] != current_node.cost:
                return fail()
            if data["incumbent_cost"] != expected_incumbent:
                return fail()
            if current_node.cost < expected_incumbent:
                return fail()
            del open_nodes[node_path]
            index += 1
        elif step_type == "complete":
            computations += 1
            if current_node.cost >= expected_incumbent:
                return fail()
            if current_node.visited != tsp.size - 1:
                return fail()
            if data["parent_vertex"] != current_node.vertex:
                return fail()
            if data["parent_lower_bound"] != current_node.cost:
                return fail()
            if data["selected_neighbour"] != 0:
                return fail()
            final_edge = tsp.matrix[current_node.vertex][0]
            if final_edge == utils.inf:
                return fail()
            if data["edge_cost"] != final_edge:
                return fail()
            expected_path = current_node.path + [0]
            if data["child_path"] != expected_path:
                return fail()
            if data["reduction_cost"] is not None:
                return fail()
            if data["child_lower_bound"] is not None:
                return fail()
            if data["pruned"]:
                return fail()
            if data["incumbent_cost"] != expected_incumbent:
                return fail()

            # Reconstruct incumbent updates from verified edges, not prover claims.
            completed_cost = current_node.total_cost + final_edge
            del open_nodes[node_path]
            if completed_cost < expected_incumbent:
                expected_incumbent = completed_cost
                expected_best_path = expected_path
            index += 1
        elif step_type == "dead_end":
            computations += 1
            if current_node.cost >= expected_incumbent:
                return fail()
            if data["vertex"] != current_node.vertex:
                return fail()
            if data["lower_bound"] != current_node.cost:
                return fail()
            if data["incumbent_cost"] != expected_incumbent:
                return fail()
            if current_node.visited == tsp.size - 1:
                final_edge = tsp.matrix[current_node.vertex][0]
                if final_edge != utils.inf:
                    return fail()
                if data.get("reason") != "no_return_edge":
                    return fail()
            else:
                legal_children = []
                for destination in range(current_node.size):
                    if (
                        current_node.matrix[current_node.vertex][destination]
                        == utils.inf
                    ):
                        continue
                    if destination in current_node.path:
                        continue
                    legal_children.append(destination)
                if legal_children:
                    return fail()
                if data.get("reason") != "no_children":
                    return fail()
            del open_nodes[node_path]
            index += 1

    # A truncated transcript cannot pass while any generated node remains open.
    if open_nodes:
        return fail()
    if expected_best_path is None:
        return fail()

    # The submitted tour was checked separately; equal-cost alternative tours are valid.
    if expected_incumbent != proposed_cost:
        return fail()
    return (True, computations, expected_best_path, expected_incumbent)


def _parallel_hash_validation(transcript, validators, transcript_root, host_workers=1,
                              parallel_threshold=10000):
    """Partition the chain into contiguous slices and combine their checks and modeled
    times.
    """
    if transcript is None:
        return (False, 0, 0.0)
    steps = transcript.steps
    total_steps = len(steps)
    if total_steps == 0 or not validators:
        return (False, 0, 0.0)

    # Avoid assigning empty hash slices when there are more validators than records.
    validators = validators[: min(len(validators), total_steps)]
    num_validators = len(validators)
    initial_hash = transcript_root
    arguments = []
    base_size = total_steps // num_validators
    remainder = total_steps % num_validators
    current_index = 0
    for validator_index in range(num_validators):
        slice_size = base_size
        if validator_index < remainder:
            slice_size += 1
        start_index = current_index
        end_index = start_index + slice_size
        if start_index == 0:
            slice_initial_hash = initial_hash
        else:

            # The preceding slice also verifies this boundary hash.
            slice_initial_hash = steps[start_index - 1]["hash"]
        arguments.append(
            (validator_index, steps[start_index:end_index], start_index, slice_initial_hash)
        )
        current_index = end_index
    # Small certificates cost less to check directly than to send to fresh workers.
    workers = host_workers if total_steps >= parallel_threshold else 1
    results = host_map(_hash_slice_worker, arguments, workers)
    all_valid = True
    total_computations = 0
    validator_times = []
    for validator_index, valid, computations, failed_index in results:
        validator = validators[validator_index]
        total_computations += computations
        if validator.hash_validation_rate > 0:
            validator_time = computations / validator.hash_validation_rate
        else:
            validator_time = 0.0
        validator_times.append(validator_time)
        if not valid:
            all_valid = False
    validation_time = max(validator_times) if validator_times else 0.0
    return (all_valid, total_computations, validation_time)


def _hash_slice_worker(args):
    """Check step numbers, previous-hash links, and recomputed hashes in one assigned
    slice.
    """
    validator_index, steps, start_index, initial_hash = args
    previous_hash = initial_hash
    computations = 0
    for offset, step in enumerate(steps):
        check_cancelled()
        index = start_index + offset
        computations += 1
        expected_step_number = index + 1
        if step["step"] != expected_step_number:
            return (validator_index, False, computations, index)
        if step["previous_hash"] != previous_hash:
            return (validator_index, False, computations, index)
        hash_data = previous_hash + str(step["step"]) + str(step["data"])
        expected_hash = utils.create_hash(hash_data)
        if step["hash"] != expected_hash:
            return (validator_index, False, computations, index)
        previous_hash = step["hash"]
    return (validator_index, True, computations, None)


def _validate_hamiltonian_cycle(tsp, path, debug=True):
    """Require integer city indices and exactly one visit per city before returning to
    zero.
    """

    # A cycle contains each city once, plus zero repeated at the end.
    if not isinstance(path, (list, tuple)) or len(path) != tsp.size + 1:
        return False

    # Reject Boolean and floating-point indices before they reach matrix indexing.
    if any((type(vertex) is not int or not 0 <= vertex < tsp.size for vertex in path)):
        return False
    return path[0] == 0 and path[-1] == 0 and (len(set(path[:-1])) == tsp.size)


def _validate_proposed_tour(tsp, path, proposed_cost):
    """Validate the actual submitted cycle, independently of its transcript.

    Alternative equal-cost optimum tours are permitted by the protocol.
    """
    if not _validate_hamiltonian_cycle(tsp, path, debug=False):
        return False
    if isinstance(proposed_cost, bool) or not isinstance(proposed_cost, Real):
        return False
    if not math.isfinite(proposed_cost):
        return False
    total = 0
    for source, destination in zip(path, path[1:]):
        edge = tsp.matrix[source][destination]
        if (
            isinstance(edge, bool)
            or not isinstance(edge, Real)
            or (not math.isfinite(edge))
        ):
            return False
        total += edge
    return total == proposed_cost


def _validate_transcript_root(
    tsp, transcript, transcript_sigma, transcript_root, debug=True
):
    """Reconstruct the trusted root and its children, then check the supplied
    commitment.
    """
    if not hasattr(transcript, "root"):
        return False
    root = tsp.tsp_root
    expected_children = []
    for neighbour in range(root.size):
        if root.matrix[root.vertex][neighbour] == utils.inf:
            continue
        if neighbour in root.path:
            continue
        child = TspFunction._create_child(root, tsp.matrix, root.vertex, neighbour)
        edge_cost = tsp.matrix[root.vertex][neighbour]
        reduced_edge_cost = root.matrix[root.vertex][neighbour]
        reduction_cost = child.cost - root.cost - reduced_edge_cost
        expected_children.append(
            {
                "selected_neighbour": neighbour,
                "child_path": child.path[:],
                "edge_cost": edge_cost,
                "reduction_cost": reduction_cost,
                "child_lower_bound": child.cost,
            }
        )

    # The root is reconstructed from trusted TSP state rather than copied from evidence.
    expected_root_data = {
        "path": root.path[:],
        "vertex": root.vertex,
        "visited": root.visited,
        "lower_bound": root.cost,
        "children": expected_children,
    }
    if transcript.root["data"] != expected_root_data:
        return False
    if transcript.root["step"] != 0:
        return False
    if transcript.root["previous_hash"] is not None:
        return False
    calculated_root_hash = utils.create_hash(
        transcript_sigma.hex() + str(expected_root_data) + str(tsp.matrix)
    )
    if calculated_root_hash != transcript_root:
        return False
    if transcript.root["hash"] != transcript_root:
        return False
    return True
