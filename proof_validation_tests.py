
import copy
import secrets

import utils

from nodes import Node
from tspData import TspData
from tspFunctions import TspFunction
from transcript import Transcript
from validation import proof_based_validation


# ============================================================
# Simple fake validator
# ============================================================
#
# proof_based_validation() expects validator nodes with:
#
#   hash_validation_rate
#   semantic_validation_rate
#
# For these correctness tests we do not care about realistic
# simulated timing, only whether the proof is accepted/rejected.
#
class TestValidator:

    def __init__(self):

        self.name = "test-validator"
        self.hash_validation_rate = 100000.0
        self.semantic_validation_rate = 100000.0


# ============================================================
# Rebuild transcript hash chain after malicious modification
# ============================================================
#
# This is IMPORTANT.
#
# If we modify transcript data without rebuilding hashes,
# validation would fail only because the hash chain is broken.
#
# We want stronger tests:
#
#   "Can an attacker manufacture a NEW internally consistent
#    transcript containing false B&B claims?"
#
def rebuild_hash_chain(transcript):

    previous_hash = transcript.root["hash"]

    for index, step in enumerate(
        transcript.steps
    ):

        step_number = index + 1

        data = step["data"]

        current_hash = utils.create_hash(
            previous_hash
            + str(step_number)
            + str(data)
        )

        step["step"] = step_number
        step["previous_hash"] = previous_hash
        step["hash"] = current_hash

        previous_hash = current_hash

    transcript.previous_hash = previous_hash


# ============================================================
# Generate a genuine Proof Validation fixture
# ============================================================

def create_genuine_proof(
    size=7
):

    tsp = TspData(
        size,
        True
    )

    sigma = secrets.token_bytes(32)

    root = tsp.tsp_root

    root_children = []

    for neighbour in range(root.size):

        if (
            root.matrix[
                root.vertex
            ][neighbour]
            == utils.inf
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

        root_children.append({
            "selected_neighbour":
                neighbour,

            "child_path":
                child.path[:],

            "edge_cost":
                edge_cost,

            "reduction_cost":
                reduction_cost,

            "child_lower_bound":
                child.cost
        })

    root_data = {
        "path": root.path[:],
        "vertex": root.vertex,
        "visited": root.visited,
        "lower_bound": root.cost,
        "children": root_children
    }

    transcript_root = utils.create_hash(
        sigma.hex()
        + str(root_data)
        + str(tsp.matrix)
    )

    transcript = Transcript(
        root_data,
        transcript_root
    )

    # Generate genuine complete B&B search.
    TspFunction.tsp_solver(
        tsp,
        None,
        transcript,
        0
    )

    validators = [
        TestValidator(),
        TestValidator()
    ]

    return (
        tsp,
        tsp.best_path[:],
        tsp.best_cost,
        transcript,
        validators,
        sigma,
        transcript_root
    )


# ============================================================
# Helper
# ============================================================

def validate(
    tsp,
    path,
    cost,
    transcript,
    validators,
    sigma,
    transcript_root
):

    result = proof_based_validation(
        tsp,
        path,
        cost,
        transcript,
        validators,
        sigma,
        transcript_root
    )

    return result["valid"]


def print_result(
    name,
    actual,
    expected
):

    status = (
        "PASS"
        if actual == expected
        else "FAIL"
    )

    print(
        f"{status:5} | "
        f"{name:35} | "
        f"expected={expected} "
        f"actual={actual}"
    )

    return actual == expected

# ============================================================
# TEST 1
# Genuine transcript must pass
# ============================================================

def test_honest_proof():

    (
        tsp,
        path,
        cost,
        transcript,
        validators,
        sigma,
        transcript_root
    ) = create_genuine_proof()

    return validate(
        tsp,
        path,
        cost,
        transcript,
        validators,
        sigma,
        transcript_root
    )


# ============================================================
# TEST 2
# Astra's incomplete-tour attack
# ============================================================

def test_incomplete_tour():

    (
        tsp,
        path,
        cost,
        transcript,
        validators,
        sigma,
        transcript_root
    ) = create_genuine_proof()

    fake_path = [
        0,
        1,
        0
    ]

    return validate(
        tsp,
        fake_path,
        cost,
        transcript,
        validators,
        sigma,
        transcript_root
    )


# ============================================================
# TEST 3
# Wrong proposed cost
# ============================================================

def test_wrong_cost():

    (
        tsp,
        path,
        cost,
        transcript,
        validators,
        sigma,
        transcript_root
    ) = create_genuine_proof()

    fake_cost = (
        cost + 100
    )

    return validate(
        tsp,
        path,
        fake_cost,
        transcript,
        validators,
        sigma,
        transcript_root
    )


# ============================================================
# TEST 4
# Fake child lower bound with VALID rebuilt hash chain
# ============================================================

def test_fake_lower_bound():

    (
        tsp,
        path,
        cost,
        transcript,
        validators,
        sigma,
        transcript_root
    ) = create_genuine_proof()

    fake_transcript = copy.deepcopy(
        transcript
    )

    # Find first branch record.
    for step in fake_transcript.steps:

        data = step["data"]

        if data.get("type") == "branch":

            data[
                "child_lower_bound"
            ] = -999

            break

    # Attacker rebuilds a perfectly consistent hash chain.
    rebuild_hash_chain(
        fake_transcript
    )

    return validate(
        tsp,
        path,
        cost,
        fake_transcript,
        validators,
        sigma,
        transcript_root
    )

# ============================================================
# TEST 5
# Fabricated reduction cost
# ============================================================

def test_fake_reduction_cost():

    (
        tsp,
        path,
        cost,
        transcript,
        validators,
        sigma,
        transcript_root
    ) = create_genuine_proof()

    fake_transcript = copy.deepcopy(
        transcript
    )

    for step in fake_transcript.steps:

        data = step["data"]

        if data.get("type") == "branch":

            data["reduction_cost"] = -999
            break

    rebuild_hash_chain(
        fake_transcript
    )

    return validate(
        tsp,
        path,
        cost,
        fake_transcript,
        validators,
        sigma,
        transcript_root
    )


# ============================================================
# TEST 6
# Fake pruning decision
# ============================================================

def test_fake_prune():

    (
        tsp,
        path,
        cost,
        transcript,
        validators,
        sigma,
        transcript_root
    ) = create_genuine_proof()

    fake_transcript = copy.deepcopy(
        transcript
    )

    changed = False

    for step in fake_transcript.steps:

        data = step["data"]

        if data.get("type") == "branch":

            data["pruned"] = not data["pruned"]
            changed = True
            break

    if not changed:
        raise RuntimeError(
            "Could not find branch for fake-prune test."
        )

    rebuild_hash_chain(
        fake_transcript
    )

    return validate(
        tsp,
        path,
        cost,
        fake_transcript,
        validators,
        sigma,
        transcript_root
    )


# ============================================================
# TEST 7
# Delete one legal child from an expansion
# ============================================================

def test_missing_child():

    (
        tsp,
        path,
        cost,
        transcript,
        validators,
        sigma,
        transcript_root
    ) = create_genuine_proof()

    fake_transcript = copy.deepcopy(
        transcript
    )

    # Find two consecutive branch records belonging
    # to the same parent. Removing one means the
    # expansion no longer contains every legal child.
    remove_index = None

    for i in range(
        len(fake_transcript.steps) - 1
    ):

        first = (
            fake_transcript.steps[i]["data"]
        )

        second = (
            fake_transcript.steps[i + 1]["data"]
        )

        if (
            first.get("type") == "branch"
            and second.get("type") == "branch"
            and first["parent_path"]
            == second["parent_path"]
        ):

            remove_index = i + 1
            break

    if remove_index is None:
        raise RuntimeError(
            "Could not find multi-child expansion."
        )

    del fake_transcript.steps[
        remove_index
    ]

    rebuild_hash_chain(
        fake_transcript
    )

    return validate(
        tsp,
        path,
        cost,
        fake_transcript,
        validators,
        sigma,
        transcript_root
    )


# ============================================================
# TEST 8
# Truncate transcript
# ============================================================

def test_truncated_transcript():

    (
        tsp,
        path,
        cost,
        transcript,
        validators,
        sigma,
        transcript_root
    ) = create_genuine_proof()

    fake_transcript = copy.deepcopy(
        transcript
    )

    cut = (
        len(fake_transcript.steps)
        // 2
    )

    fake_transcript.steps = (
        fake_transcript.steps[:cut]
    )

    rebuild_hash_chain(
        fake_transcript
    )

    return validate(
        tsp,
        path,
        cost,
        fake_transcript,
        validators,
        sigma,
        transcript_root
    )


# ============================================================
# TEST 9
# Earlier valid incumbent instead of final optimum
# ============================================================

def test_valid_but_nonoptimal_solution():

    (
        tsp,
        optimal_path,
        optimal_cost,
        transcript,
        validators,
        sigma,
        transcript_root
    ) = create_genuine_proof()

    # --------------------------------------------------------
    # Construct another VALID Hamiltonian cycle.
    #
    # Start from the genuine optimum and swap two internal
    # cities until the resulting tour has a different cost.
    # --------------------------------------------------------

    fake_path = None
    fake_cost = None

    for i in range(1, len(optimal_path) - 2):

        for j in range(i + 1, len(optimal_path) - 1):

            candidate = optimal_path[:]

            candidate[i], candidate[j] = (
                candidate[j],
                candidate[i]
            )

            candidate_cost = 0
            valid = True

            for k in range(
                len(candidate) - 1
            ):

                edge_cost = tsp.matrix[
                    candidate[k]
                ][
                    candidate[k + 1]
                ]

                if edge_cost == utils.inf:
                    valid = False
                    break

                candidate_cost += edge_cost

            if (
                valid
                and candidate_cost != optimal_cost
            ):

                fake_path = candidate
                fake_cost = candidate_cost
                break

        if fake_path is not None:
            break

    if fake_path is None:

        raise RuntimeError(
            "Could not construct a valid "
            "non-optimal Hamiltonian cycle."
        )

    print(
        "Non-optimal solution test:",
        fake_cost,
        "vs optimum:",
        optimal_cost
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # fake_path is structurally valid.
    # fake_cost is also CORRECT for that path.
    #
    # The only thing wrong with it is that it is not the
    # final optimum reconstructed by the transcript.
    # --------------------------------------------------------

    return validate(
        tsp,
        fake_path,
        fake_cost,
        transcript,
        validators,
        sigma,
        transcript_root
    )

# ============================================================
# TEST 10
# Reorder records in a way inconsistent with incumbent history
# ============================================================

def test_invalid_incumbent_history():

    (
        tsp,
        path,
        cost,
        transcript,
        validators,
        sigma,
        transcript_root
    ) = create_genuine_proof()

    fake_transcript = copy.deepcopy(
        transcript
    )

    # Find two distinct processing groups.
    #
    # We only swap simple single-record prune/complete/dead-end
    # entries because branch expansions may consist of several
    # consecutive records belonging to one parent.

    candidate_indices = []

    for i, step in enumerate(
        fake_transcript.steps
    ):

        data = step["data"]

        if data.get("type") in (
            "prune",
            "complete",
            "dead_end"
        ):
            candidate_indices.append(i)

    swapped = False

    for a in range(
        len(candidate_indices)
    ):

        for b in range(
            a + 1,
            len(candidate_indices)
        ):

            i = candidate_indices[a]
            j = candidate_indices[b]

            data_i = (
                fake_transcript.steps[i]["data"]
            )

            data_j = (
                fake_transcript.steps[j]["data"]
            )

            # Only use records referring to different nodes.
            path_i = (
                tuple(data_i.get(
                    "path",
                    data_i.get("parent_path", [])
                ))
            )

            path_j = (
                tuple(data_j.get(
                    "path",
                    data_j.get("parent_path", [])
                ))
            )

            if path_i == path_j:
                continue

            fake_transcript.steps[i], \
            fake_transcript.steps[j] = (
                fake_transcript.steps[j],
                fake_transcript.steps[i]
            )

            swapped = True
            break

        if swapped:
            break

    if not swapped:
        raise RuntimeError(
            "Could not find records for incumbent-history test."
        )

    rebuild_hash_chain(
        fake_transcript
    )

    return validate(
        tsp,
        path,
        cost,
        fake_transcript,
        validators,
        sigma,
        transcript_root
    )

if __name__ == "__main__":

    print(
        "\n"
        "==============================================="
    )

    print(
        "PROOF VALIDATION ADVERSARIAL TESTS"
    )

    print(
        "===============================================\n"
    )

    results = []

    # --------------------------------------------------------
    # Honest baseline
    # --------------------------------------------------------

    results.append(
        print_result(
            "Honest transcript",
            test_honest_proof(),
            True
        )
    )

    # --------------------------------------------------------
    # Structural / proposed-solution attacks
    # --------------------------------------------------------

    results.append(
        print_result(
            "Incomplete Hamiltonian tour",
            test_incomplete_tour(),
            False
        )
    )

    results.append(
        print_result(
            "Wrong proposed cost",
            test_wrong_cost(),
            False
        )
    )

    # --------------------------------------------------------
    # Fabricated B&B evidence
    # --------------------------------------------------------

    results.append(
        print_result(
            "Fabricated lower bound",
            test_fake_lower_bound(),
            False
        )
    )

    results.append(
        print_result(
            "Fabricated reduction cost",
            test_fake_reduction_cost(),
            False
        )
    )

    results.append(
        print_result(
            "Fabricated pruning decision",
            test_fake_prune(),
            False
        )
    )

    # --------------------------------------------------------
    # Search completeness attacks
    # --------------------------------------------------------

    results.append(
        print_result(
            "Missing legal child",
            test_missing_child(),
            False
        )
    )

    results.append(
        print_result(
            "Truncated transcript",
            test_truncated_transcript(),
            False
        )
    )

    # --------------------------------------------------------
    # Incumbent / execution-order attacks
    # --------------------------------------------------------

    results.append(
        print_result(
            "Valid non-optimal solution",
            test_valid_but_nonoptimal_solution(),
            False
        )
    )

    results.append(
        print_result(
            "Invalid incumbent history",
            test_invalid_incumbent_history(),
            False
        )
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print(
        "\n"
        "==============================================="
    )

    print(
        f"PASSED: {sum(results)} / {len(results)}"
    )

    print(
        "===============================================\n"
    )

    if not all(results):

        raise RuntimeError(
            "One or more Proof Validation "
            "security tests failed."
        )