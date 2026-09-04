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

def benchmark_pow(duration=1.0):

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

def benchmark_tsp_pouw(duration=1.0, size=0):

    # Create a TSP instance used for the benchmark.
    benchmark_tsp = TspData(size, True)

    # Total number of B&B search computations performed.
    total_computations = 0

    # Start measuring only the actual TSP solving process.
    start = time.perf_counter()

    # Repeatedly execute the TSP solver until the
    # requested benchmark duration has passed.
    while time.perf_counter() - start < duration:

        # Solve the TSP instance using the Branch and Bound
        # algorithm. The first returned value represents
        # the number of computational operations performed.
        computations, _, _, _ = TspFunction.tsp_solver(
            benchmark_tsp,
            1
        )

        # Add the computations performed during this
        # solver execution to the total.
        total_computations += computations

    # Measure the actual elapsed benchmark time.
    elapsed = time.perf_counter() - start

    # Calculate the number of B&B computations
    # that can be performed per second.
    computation_rate = total_computations / elapsed

    return computation_rate


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

    # Create a transcript that will be used to benchmark
    # the creation of transcript steps.
    transcript = Transcript()

    # Number of transcript steps created.
    computations = 0

    # Start measuring the benchmark duration.
    start = time.perf_counter()

    # Continue creating transcript steps until
    # the requested duration has passed.
    while time.perf_counter() - start < duration:

        # Create one representative transcript step.
        data = Transcript.create_step_data(
            parent_path=[0, 1, 2, 3],
            parent_vertex=3,
            parent_lower_bound=500,
            selected_neighbour=4,
            child_path=[0, 1, 2, 3, 4],
            edge_cost=70,
            reduction_cost=30,
            child_lower_bound=600,
            pruned=False
        )

        # Add the generated step to the transcript.
        transcript.add_step(data)

        # Count the completed transcript operation.
        computations += 1

    # Measure the actual elapsed benchmark time.
    elapsed = time.perf_counter() - start

    # Calculate the transcript-step creation rate.
    computation_rate = computations / elapsed

    return computation_rate


# =========================================================
# PoUW path validation benchmark
# =========================================================

def benchmark_path_validation(duration=1.0, size=11):

    # Create the TSP instance used for the benchmark.
    tsp = TspData(size, True)

    # Use a known valid TSP path.
    path = [0, 8, 3, 6, 10, 2, 1, 5, 9, 7, 4, 0]

    # Expected cost associated with the proposed path.
    proposed_cost = 330

    # Create a transcript containing the steps
    # corresponding to the proposed path.
    transcript = Transcript()

    for i in range(len(path) - 1):

        # Get the source and destination vertices
        # for the current path edge.
        source = path[i]
        destination = path[i + 1]

        # Create a transcript step representing
        # this path transition.
        data = Transcript.create_step_data(
            parent_path=path[:i + 1],
            parent_vertex=source,
            parent_lower_bound=0,
            selected_neighbour=destination,
            child_path=path[:i + 2],
            edge_cost=tsp.matrix[source][destination],
            reduction_cost=0,
            child_lower_bound=0,
            pruned=False
        )

        # Add the step to the transcript.
        transcript.add_step(data)

    # Number of complete path validations performed.
    computations = 0

    # Start measuring the benchmark duration.
    start = time.perf_counter()

    # Repeatedly validate the complete path until
    # the requested benchmark duration has passed.
    while time.perf_counter() - start < duration:

        validation._validate_calculated_path(
            tsp,
            path,
            proposed_cost,
            transcript
        )

        # One complete path validation was performed.
        computations += 1

    # Measure the actual elapsed benchmark time.
    elapsed = time.perf_counter() - start

    # Calculate the number of complete path
    # validations that can be performed per second.
    validation_rate = computations / elapsed

    return validation_rate


# =========================================================
# PoUW hash-chain validation benchmark
# =========================================================

def benchmark_hash_validation(duration=1.0, steps=1000):

    # Create a transcript containing a fixed number
    # of valid transcript steps.
    transcript = Transcript()

    for _ in range(steps):

        # Create one representative transcript step.
        data = Transcript.create_step_data(
            parent_path=[0, 1, 2, 3],
            parent_vertex=3,
            parent_lower_bound=500,
            selected_neighbour=4,
            child_path=[0, 1, 2, 3, 4],
            edge_cost=70,
            reduction_cost=30,
            child_lower_bound=600,
            pruned=False
        )

        # Add the step to the transcript.
        transcript.add_step(data)

    # Create the arguments expected by the hash-slice
    # validation worker.
    arguments = (
        0,
        transcript.steps,
        0,
        steps,
        utils.create_hash(transcript.sigma)
    )

    # Total number of transcript steps successfully checked.
    computations = 0

    # Start measuring the benchmark duration.
    start = time.perf_counter()

    # Repeatedly validate the entire transcript hash chain
    # until the requested benchmark duration has passed.
    while time.perf_counter() - start < duration:

        (
            _,
            valid,
            steps_checked,
            _
        ) = validation._hash_slice_worker(arguments)

        # Stop the benchmark if the generated transcript
        # unexpectedly fails hash validation.
        if not valid:
            break

        # Add the number of successfully checked steps.
        computations += steps_checked

    # Measure the actual elapsed benchmark time.
    elapsed = time.perf_counter() - start

    # Calculate the number of transcript hash-chain
    # validation steps that can be checked per second.
    validation_rate = computations / elapsed

    return validation_rate