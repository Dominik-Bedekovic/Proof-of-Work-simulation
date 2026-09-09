from nodes import Node
from blockFunctions import BlockFunctions
from tspData import TspData
from tspFunctions import TspFunction
from transcript import Transcript
import validation
import utils
import time
import secrets


# Validation modes used by the simulation.
NO_VALIDATION = 0b00
PROOF_VALIDATION = 0b01
COUNCIL_VALIDATION = 0b10


# =========================================================
# PoW benchmark
# =========================================================

def benchmark_pow(duration=2.0):

    # Create a temporary node whose block data is used
    # as the input for the SHA-256 hashing benchmark.
    benchmark_node = Node("benchmark")

    # Number of hashes successfully calculated.
    hashes = 0

    # Start measuring the benchmark duration.
    start = time.perf_counter()

    # Continue hashing until the requested duration has passed.
    while time.perf_counter() - start < duration:

        # Perform one block-header hash.
        BlockFunctions.create_header_hash(
            benchmark_node.blockData.previous_hash,
            benchmark_node.blockData.timestamp,
            benchmark_node.merkle_root,
            benchmark_node.nonce
        )

        # Change the nonce so that the next iteration
        # represents a different hash attempt.
        benchmark_node.nonce += 1

        # Count the completed hash.
        hashes += 1

    # Measure the actual elapsed benchmark time.
    elapsed = time.perf_counter() - start

    # Calculate the number of hashes that can be
    # performed per second.
    hash_rate = hashes / elapsed

    return hash_rate


# =========================================================
# PoUW TSP benchmark
# =========================================================

def benchmark_tsp_pouw(duration=2.0, size=0):

    total_computations = 0
    elapsed = 0.0

    while elapsed < duration:

        benchmark_tsp = TspData(size, True)

        start = time.perf_counter()

        computations, _, _, finished = TspFunction.tsp_solver(
            benchmark_tsp
        )

        elapsed += time.perf_counter() - start
        total_computations += computations

    return total_computations / elapsed

def benchmark_initial_validation(duration=2.0, size=0):

    # Obtain a genuine valid solution.
    solved_tsp = TspData(size, True)

    TspFunction.tsp_solver(
        solved_tsp
    )

    proposed_path = solved_tsp.best_path
    proposed_cost = solved_tsp.best_cost

    benchmark_tsp = TspData(size, True)

    validations = 0
    start = time.perf_counter()

    while time.perf_counter() - start < duration:

        valid = validation._validate_node(
            (
                benchmark_tsp,
                proposed_path,
                proposed_cost
            )
        )

        if not valid:
            raise RuntimeError(
                "Benchmark initial validation failed."
            )

        validations += 1

    elapsed = time.perf_counter() - start

    return validations / elapsed

def benchmark_branch_validation(duration=2.0, size=0):

    # Solve deterministic benchmark instance once
    # to obtain a genuine proposed optimum.
    solved_tsp = TspData(size, True)

    TspFunction.tsp_solver(
        solved_tsp
    )

    proposed_cost = solved_tsp.best_cost

    # Fresh equivalent deterministic instance.
    benchmark_tsp = TspData(size, True)

    branches = TspFunction.create_initial_branches(
        benchmark_tsp
    )

    total_computations = 0
    start = time.perf_counter()

    branch_index = 0

    while time.perf_counter() - start < duration:

        branch = branches[branch_index]

        valid, computations = (
            TspFunction.validate_branch(
                benchmark_tsp,
                branch,
                proposed_cost
            )
        )

        if not valid:
            raise RuntimeError(
                "Benchmark branch validation failed."
            )

        total_computations += computations

        branch_index = (
            branch_index + 1
        ) % len(branches)

    elapsed = time.perf_counter() - start

    return (
        total_computations / elapsed
    )

def _create_proof_benchmark_transcript(size):

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
        "path":
            root.path[:],

        "vertex":
            root.vertex,

        "visited":
            root.visited,

        "lower_bound":
            root.cost,

        "children":
            root_children
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

    # Generate a genuine Proof transcript.
    TspFunction.tsp_solver(
        tsp,
        None,
        transcript,
        0
    )

    return (
        tsp,
        transcript,
        sigma,
        transcript_root
    )

# =========================================================
# PoUW transcript benchmark
# =========================================================

def benchmark_transcript(
    duration=2.0,
    size=10
):

    (
        tsp,
        source_transcript,
        sigma,
        transcript_root
    ) = _create_proof_benchmark_transcript(
        size
    )

    source_steps = (
        source_transcript.steps
    )

    if not source_steps:
        return 0.0

    computations = 0

    start = time.perf_counter()

    while (
        time.perf_counter() - start
        < duration
    ):

        benchmark_transcript = Transcript(
            source_transcript.root["data"],
            transcript_root
        )

        for source_step in source_steps:

            if (
                time.perf_counter()
                - start
                >= duration
            ):
                break

            data = source_step["data"]

            benchmark_transcript.add_step(
                data
            )

            computations += 1

    elapsed = (
        time.perf_counter()
        - start
    )

    if elapsed <= 0:
        return 0.0

    return (
        computations
        / elapsed
    )

# =========================================================
# PoUW hash-chain validation benchmark
# =========================================================

def benchmark_hash_validation(
    duration=2.0,
    size=10
):

    (
        tsp,
        transcript,
        sigma,
        transcript_root
    ) = _create_proof_benchmark_transcript(
        size
    )

    total_steps = len(
        transcript.steps
    )

    if total_steps == 0:
        return 0.0

    arguments = (
        0,
        transcript.steps,
        0,
        total_steps,
        transcript_root
    )

    computations = 0

    start = time.perf_counter()

    while (
        time.perf_counter() - start
        < duration
    ):

        (
            _,
            valid,
            steps_checked,
            _
        ) = validation._hash_slice_worker(
            arguments
        )

        if not valid:
            raise RuntimeError(
                "Hash validation benchmark "
                "generated an invalid transcript."
            )

        computations += (
            steps_checked
        )

    elapsed = (
        time.perf_counter()
        - start
    )

    if elapsed <= 0:
        return 0.0

    return (
        computations
        / elapsed
    )

def benchmark_semantic_validation(
    duration=2.0,
    size=10
):

    (
        tsp,
        transcript,
        transcript_sigma,
        transcript_root
    ) = _create_proof_benchmark_transcript(
        size
    )

    proposed_path = (
        tsp.best_path[:]
    )

    proposed_cost = (
        tsp.best_cost
    )

    if not proposed_path:
        raise RuntimeError(
            "Semantic validation benchmark "
            "did not generate a TSP solution."
        )

    total_units = 0

    start = time.perf_counter()

    while (
        time.perf_counter() - start
        < duration
    ):

        # =====================================================
        # 1. HAMILTONIAN VALIDATION
        # =====================================================

        hamiltonian_valid = (
            validation
            ._validate_hamiltonian_cycle(
                tsp,
                proposed_path,
                debug=False
            )
        )

        if not hamiltonian_valid:
            raise RuntimeError(
                "Semantic validation benchmark "
                "generated an invalid Hamiltonian cycle."
            )

        # =====================================================
        # 2. AUTHENTICATED ROOT VALIDATION
        # =====================================================

        root_valid = (
            validation
            ._validate_transcript_root(
                tsp,
                transcript,
                transcript_sigma,
                transcript_root,
                debug=False
            )
        )

        if not root_valid:
            raise RuntimeError(
                "Semantic validation benchmark "
                "generated an invalid transcript root."
            )

        # =====================================================
        # 3. COMPLETE SEMANTIC B&B REPLAY
        # =====================================================

        (
            semantic_valid,
            replay_checks,
            reconstructed_path,
            reconstructed_cost
        ) = (
            validation
            ._validate_transcript_semantics(
                tsp,
                transcript,
                proposed_path,
                proposed_cost,
                debug=False
            )
        )

        if not semantic_valid:
            raise RuntimeError(
                "Semantic validation benchmark "
                "generated an invalid B&B transcript."
            )

        if (
            reconstructed_path
            != proposed_path
        ):
            raise RuntimeError(
                "Semantic validation benchmark "
                "reconstructed the wrong path."
            )

        if (
            reconstructed_cost
            != proposed_cost
        ):
            raise RuntimeError(
                "Semantic validation benchmark "
                "reconstructed the wrong cost."
            )

        # =====================================================
        # COUNT THE EXACT SAME SEMANTIC UNITS
        # USED BY proof_based_validation()
        # =====================================================

        total_units += (
            _semantic_validation_units(
                transcript,
                replay_checks
            )
        )

    elapsed = (
        time.perf_counter()
        - start
    )

    if elapsed <= 0:
        return 0.0

    return (
        total_units
        / elapsed
    )

def _semantic_validation_units(
    transcript,
    replay_checks
):

    root_children = (
        transcript
        .root["data"]
        .get(
            "children",
            []
        )
    )

    hamiltonian_units = 1
    root_fixed_units = 1
    root_child_units = len(
        root_children
    )

    return (
        hamiltonian_units
        + root_fixed_units
        + root_child_units
        + replay_checks
    )