from nodes import Node
from blockFunctions import BlockFunctions
from tspData import TspData
from tspFunctions import TspFunction
from transcript import Transcript
import validation
import utils
import time

NO_VALIDATION = 0b00
PROOF_VALIDATION = 0b01
COUNCIL_VALIDATION = 0b10

# Measures the SHA-256 hashing rate used as the
# computational workload for the PoW simulation.
def benchmark_pow(duration=1.0):

    print("\n--- PoW benchmark ---")
    print(f"Benchmark duration: {duration:.2f}s")

    benchmark_node = Node("benchmark")

    hashes = 0

    start = time.perf_counter()

    while time.perf_counter() - start < duration:

        BlockFunctions.create_header_hash(
            benchmark_node.blockData.previous_hash,
            benchmark_node.blockData.timestamp,
            benchmark_node.merkle_root,
            benchmark_node.nonce
        )

        benchmark_node.nonce += 1
        hashes += 1

    elapsed = time.perf_counter() - start
    hash_rate = hashes / elapsed

    print(f"Elapsed time: {elapsed:.4f}s")
    print(f"Hashes performed: {hashes}")
    print(f"Hash rate: {hash_rate:.2f} hashes/s")

    return hash_rate


# Measures the Branch and Bound search-node processing rate
# used as the computational workload for the PoUW simulation.
def benchmark_tsp_pouw(duration=1.0, size=0):

    print("\n--- PoUW TSP benchmark ---")
    print(f"Benchmark duration: {duration:.2f}s")
    print(f"TSP size: {size} cities")

    # Create a TSP instance.
    benchmark_tsp = TspData(size, True)

    total_computations = 0

    # Start measuring only the actual B&B search.
    start = time.perf_counter()

    while (time.perf_counter() - start < duration):

        computations, _, _, _= TspFunction.tsp_solver(benchmark_tsp, 1)

        total_computations += computations


    elapsed = time.perf_counter() - start
    computation_rate = total_computations / elapsed

    print(f"Elapsed time: {elapsed:.4f}s")
    print(f"Computations performed: {total_computations}")
    print(
        f"Computation rate: "
        f"{computation_rate:.2f} computations/s"
    )

    return computation_rate

def benchmark_validation(duration=1.0, size=0):
    print("\n--- PoUW validation benchmark ---")
    print(f"Benchmark duration: {duration:.2f}s")
    print(f"TSP size: {size} cities")

    # Create ONE fixed TSP instance
    benchmark_tsp = TspData(size, True)

    # Get the branches that the council validator would check
    branches = TspFunction.create_initial_branches(benchmark_tsp)

    # Use a fixed proposed cost
    proposed_cost = 330

    validations = 0

    start = time.perf_counter()

    while time.perf_counter() - start < duration:

        for branch in branches:

            TspFunction.validate_branch(
                benchmark_tsp,
                branch,
                proposed_cost
            )

            validations += 1

            if time.perf_counter() - start >= duration:
                break

    elapsed = time.perf_counter() - start

    validation_rate = validations / elapsed

    print(f"Elapsed time: {elapsed:.4f}s")
    print(f"Validations performed: {validations}")
    print(f"Validation rate: {validation_rate:.2f} validations/s")

    return validation_rate

def benchmark_transcript(duration=1.0):

    print("\n--- PoUW transcript benchmark ---")
    print(f"Benchmark duration: {duration:.2f}s")

    transcript = Transcript()

    computations = 0

    start = time.perf_counter()

    while time.perf_counter() - start < duration:

        for _ in range(1):
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

            transcript.add_step(data)

            computations += 1

    elapsed = time.perf_counter() - start

    computation_rate = computations / elapsed

    print(f"Elapsed time: {elapsed:.4f}s")
    print(f"Transcript steps: {computations}")
    print(f"Transcript rate: {computation_rate:.2f} steps/s")

    return computation_rate

def benchmark_path_validation(duration=1.0, size=11):

    print("\n--- PoUW path validation benchmark ---")
    print(f"Benchmark duration: {duration:.2f}s")
    print(f"TSP size: {size} cities")

    # Create the TSP instance.
    tsp = TspData(size, True)

    # Use a known valid path and cost.
    path = [0, 8, 3, 6, 10, 2, 1, 5, 9, 7, 4, 0]
    proposed_cost = 330

    # Create a transcript containing the required path steps.
    transcript = Transcript()

    for i in range(len(path) - 1):

        source = path[i]
        destination = path[i + 1]

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

        transcript.add_step(data)

    # Start benchmark.
    computations = 0

    start = time.perf_counter()

    while time.perf_counter() - start < duration:

        validation._validate_calculated_path(
            tsp,
            path,
            proposed_cost,
            transcript
        )

        computations += 1

    elapsed = time.perf_counter() - start

    validation_rate = computations / elapsed

    print(f"Elapsed time: {elapsed:.4f}s")
    print(f"Validations performed: {computations}")
    print(
        f"Validation rate: "
        f"{validation_rate:.2f} validations/s"
    )

    return validation_rate

def benchmark_hash_validation(duration=1.0, steps=1000):

    print("\n--- PoUW hash validation benchmark ---")
    print(f"Benchmark duration: {duration:.2f}s")
    print(f"Transcript steps: {steps}")

    transcript = Transcript()

    # Create a fixed valid transcript
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
            pruned=False
        )

        transcript.add_step(data)

    arguments = (
        0,
        transcript.steps,
        0,
        steps,
        utils.create_hash(transcript.sigma)
    )

    computations = 0

    start = time.perf_counter()

    while time.perf_counter() - start < duration:

        (
            _,
            valid,
            steps_checked,
            _
        ) = validation._hash_slice_worker(arguments)

        if not valid:
            print("Hash validation failed!")
            break

        computations += steps_checked

    elapsed = time.perf_counter() - start

    validation_rate = computations / elapsed

    print(f"Elapsed time: {elapsed:.4f}s")
    print(f"Hash steps checked: {computations}")
    print(f"Validation rate: {validation_rate:.2f} steps/s")

    return validation_rate