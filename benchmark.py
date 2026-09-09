from nodes import Node
from blockFunctions import BlockFunctions
from tspData import TspData
from tspFunctions import TspFunction
from transcript import Transcript
import validation
import utils
import time


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

# =========================================================
# PoUW transcript benchmark
# =========================================================

def benchmark_transcript(duration=2.0):

    root_data = {
        "path": [0],
        "vertex": 0,
        "visited": 0,
        "lower_bound": 0,
        "children": []
    }

    root_hash = utils.create_hash(
        str(root_data)
    )

    transcript = Transcript(
        root_data,
        root_hash
    )

    computations = 0

    start = time.perf_counter()

    while (
        time.perf_counter() - start
        < duration
    ):

        data = Transcript.create_step_data(
            parent_path=[0, 1, 2, 3],
            parent_vertex=3,
            parent_lower_bound=500,
            selected_neighbour=4,
            child_path=[0, 1, 2, 3, 4],
            edge_cost=70,
            reduction_cost=30,
            child_lower_bound=600,
            incumbent_cost=1000,
            pruned=False
        )

        transcript.add_step(data)

        computations += 1

    elapsed = (
        time.perf_counter()
        - start
    )

    if elapsed <= 0:
        return 0.0

    computation_rate = (
        computations / elapsed
    )

    return computation_rate

# =========================================================
# PoUW hash-chain validation benchmark
# =========================================================

def benchmark_hash_validation(
    duration=2.0,
    steps=1000
):

    root_data = {
        "path": [0],
        "vertex": 0,
        "visited": 0,
        "lower_bound": 0,
        "children": []
    }

    root_hash = utils.create_hash(
        str(root_data)
    )

    transcript = Transcript(
        root_data,
        root_hash
    )

    # Generate a valid transcript hash chain.
    for _ in range(steps):

        data = Transcript.create_step_data(
            parent_path=[0, 1, 2, 3],
            parent_vertex=3,
            parent_lower_bound=500,
            selected_neighbour=4,
            child_path=[0, 1, 2, 3, 4],
            edge_cost=70,
            reduction_cost=30,
            child_lower_bound=600,
            incumbent_cost=1000,
            pruned=False
        )

        transcript.add_step(data)

    arguments = (
        0,
        transcript.steps,
        0,
        len(transcript.steps),
        root_hash
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
                "Hash validation benchmark generated "
                "an invalid transcript."
            )

        computations += steps_checked

    elapsed = (
        time.perf_counter()
        - start
    )

    if elapsed <= 0:
        return 0.0

    validation_rate = (
        computations / elapsed
    )

    return validation_rate

def benchmark_semantic_validation(
    duration=2.0,
    size=0
):

    print(
        "\n===== ENTER benchmark_semantic_validation ====="
    )

    # Create deterministic TSP instance.
    benchmark_tsp = TspData(
        size,
        True
    )

    root = benchmark_tsp.tsp_root

    root_data = {
        "path": root.path[:],
        "vertex": root.vertex,
        "visited": root.visited,
        "lower_bound": root.cost,
        "children": []
    }

    root_hash = utils.create_hash(
        "semantic-validation-benchmark"
    )

    transcript = Transcript(
        root_data,
        root_hash
    )

    # ---------------------------------------------------------
    # Generate one genuine complete B&B transcript.
    # This work is OUTSIDE the timed benchmark section.
    # ---------------------------------------------------------

    TspFunction.tsp_solver(
        benchmark_tsp,
        None,
        transcript,
        0
    )

    proposed_path = (
        benchmark_tsp.best_path
    )

    proposed_cost = (
        benchmark_tsp.best_cost
    )

    if proposed_path is None:
        raise RuntimeError(
            "Semantic benchmark failed to produce a TSP solution."
        )

    total_checks = 0

    start = time.perf_counter()

    while (
        time.perf_counter() - start
        < duration
    ):

        (
            valid,
            checks,
            _,
            _
        ) = validation._validate_transcript_semantics(
            benchmark_tsp,
            transcript,
            proposed_path,
            proposed_cost
        )

        if not valid:

            raise RuntimeError(
                "Semantic validation benchmark failed."
            )

        total_checks += checks

    elapsed = (
        time.perf_counter()
        - start
    )

    if elapsed <= 0:
        return 0.0

    rate = (
        total_checks
        / elapsed
    )

    print(
        "Semantic validation checks:",
        total_checks
    )

    print(
        "Semantic validation elapsed:",
        elapsed
    )

    print(
        "Semantic validation rate:",
        rate,
        "records/s"
    )

    print(
        "===== EXIT benchmark_semantic_validation =====\n"
    )

    return rate