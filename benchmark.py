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

# =========================================================
# PoUW branch validation benchmark
# =========================================================

def benchmark_validation(duration=1.0, size=0):

    # Create one fixed TSP instance.
    benchmark_tsp = TspData(size, True)

    # Generate the initial branches that are used
    # by the council during branch validation.
    branches = TspFunction.create_initial_branches(
        benchmark_tsp
    )

    # Use a fixed proposed cost for every validation.
    proposed_cost = 330

    # Number of branches successfully validated.
    validations = 0

    # Start measuring the benchmark duration.
    start = time.perf_counter()

    # Continue validating branches until the
    # requested benchmark duration has passed.
    while time.perf_counter() - start < duration:

        # Validate each initial branch.
        for branch in branches:

            TspFunction.validate_branch(
                benchmark_tsp,
                branch,
                proposed_cost
            )

            # One completed branch validation.
            validations += 1

            # Stop immediately when the requested
            # benchmark duration has been reached.
            if time.perf_counter() - start >= duration:
                break

    # Measure the actual elapsed benchmark time.
    elapsed = time.perf_counter() - start

    # Calculate the number of branch validations
    # that can be performed per second.
    validation_rate = validations / elapsed

    return validation_rate


# =========================================================
# PoUW transcript benchmark
# =========================================================

def benchmark_transcript(duration=1.0):

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
    duration=1.0,
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

def benchmark_bnb_validation(duration=1.0):

    # Create a fixed TSP instance for benchmarking.
    tsp = TspData(
        11,
        benchmark=True
    )

    root = tsp.tsp_root

    # Find one legal neighbour of the root.
    neighbour = None

    for candidate in range(root.size):

        if (
            root.matrix[
                root.vertex
            ][candidate] == utils.inf
        ):
            continue

        if candidate in root.path:
            continue

        neighbour = candidate
        break

    if neighbour is None:
        raise RuntimeError(
            "B&B validation benchmark could not "
            "find a valid child."
        )

    computations = 0

    start = time.perf_counter()

    while (
        time.perf_counter() - start
        < duration
    ):

        # Reconstruct the child exactly as the proof
        # validator does.
        child = TspFunction._create_child(
            root,
            tsp.matrix,
            root.vertex,
            neighbour
        )

        # Read the original edge cost.
        edge_cost = tsp.matrix[
            root.vertex
        ][neighbour]

        # Read the reduced edge cost.
        reduced_edge_cost = root.matrix[
            root.vertex
        ][neighbour]

        # Recalculate the reduction component.
        reduction_cost = (
            child.cost
            - root.cost
            - reduced_edge_cost
        )

        # Perform representative validation comparisons.
        valid = (
            child.path
            == root.path + [neighbour]
            and edge_cost != utils.inf
            and reduction_cost >= 0
        )

        if not valid:
            raise RuntimeError(
                "B&B validation benchmark "
                "generated an invalid child."
            )

        computations += 1

    elapsed = (
        time.perf_counter()
        - start
    )

    if elapsed <= 0:
        return 0.0

    return (
        computations / elapsed
    )

if __name__ == "__main__":
    print("0.5:", benchmark_tsp_pouw(0.5, 12))
    print("1.0:", benchmark_tsp_pouw(1.0, 12))
    print("2.0:", benchmark_tsp_pouw(2.0, 12))
    print("5.0:", benchmark_tsp_pouw(5.0, 12))