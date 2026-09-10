"""Store simulated worker capabilities and the shared block, TSP, and transcript state."""

from blockData import BlockData
from blockFunctions import BlockFunctions
from tspData import TspData
from tspFunctions import TspFunction
from transcript import Transcript
import utils


class Node:
    """A simulated worker; the TSP, transcript, and rate ratios are shared across
    workers.
    """

    # These class attributes intentionally hold state shared by all simulated workers.
    blockData = BlockData()
    simulation_time = 0
    found = False
    tsp = None
    transcript = None
    pouw_pow_ratio = 0.0
    initial_validation_pow_ratio = 0.0
    branch_validation_pow_ratio = 0.0
    transcript_pouw_ratio = 0.0
    hash_validation_pow_ratio = 0.0
    semantic_validation_pow_ratio = 0.0

    @classmethod
    def initialize_tsp(cls, num_of_nodes):
        """Replace the shared TSP with a newly generated instance of the requested
        size.
        """

        # Despite the legacy parameter name, this argument is the number of cities.
        cls.tsp = TspData(num_of_nodes)

    @classmethod
    def initialize_transcript(cls, root_data, root_hash):
        """Start the shared transcript from the supplied root data and commitment."""
        cls.transcript = Transcript(root_data, root_hash)

    def __init__(self, name, hash_rate=None, reward=None):
        """Initialize this worker's mining cursor, counters, and calibrated operation
        rates.
        """
        self.name = name

        # Worker-specific coinbase data gives each worker a different header search space.
        self.coinbase = {"reward": reward if reward is not None else utils.random_string(10), "extra_nonce": 0}
        self.merkle_root = BlockFunctions.calculate_merkle_root(
            self.blockData.transactions, self.coinbase
        )
        self.nonce = 0

        # This is a simulated capability, scaled to other operations using benchmark ratios.
        self.hash_rate = hash_rate if hash_rate is not None else utils.random_num(100, 1000)
        self.mining_count = 0
        self.search_credit = 0.0
        self.previous_search_credit = 0.0
        ratio = getattr(Node, "pouw_pow_ratio", 1)
        self.search_rate = self.hash_rate * ratio
        initial_validation_ratio = getattr(Node, "initial_validation_pow_ratio", 0.0)
        self.initial_validation_rate = self.hash_rate * initial_validation_ratio
        branch_validation_ratio = getattr(Node, "branch_validation_pow_ratio", 0.0)
        self.branch_validation_rate = self.hash_rate * branch_validation_ratio
        transcript_ratio = getattr(Node, "transcript_pouw_ratio", 0)
        self.transcript_rate = self.search_rate * transcript_ratio
        hash_validation_ratio = getattr(Node, "hash_validation_pow_ratio", 0)
        self.hash_validation_rate = self.hash_rate * hash_validation_ratio
        semantic_validation_ratio = getattr(Node, "semantic_validation_pow_ratio", 0.0)
        self.semantic_validation_rate = self.hash_rate * semantic_validation_ratio

        # Keep raw B&B nodes separate from work that includes transcript append overhead.
        self.computations = 0
        self.work = 0.0

    def update_pow_state(self, result):
        """Apply the completed batch count and next-attempt cursor returned by a PoW
        worker.
        """
        self.mining_count += result["hashes"]
        self.nonce = result["nonce"]
        self.coinbase["extra_nonce"] = result["extra_nonce"]
        self.merkle_root = result["merkle_root"]
        if result["found"]:
            self.header_hash = result["header_hash"]

    def pouw_mining(self):
        """Legacy batch interface using accumulated search credit; the main loop uses
        scheduler.py.
        """
        self.previous_search_credit = self.search_credit
        self.search_credit += self.search_rate
        operations = int(self.search_credit)
        self.search_credit -= operations
        transcript = Node.transcript
        temp_computation, work, transcript_time, finished = TspFunction.tsp_solver(
            self.tsp, operations, transcript, Node.transcript_pouw_ratio
        )
        self.work += work
        self.computations += temp_computation
        return (self.computations, self.work, transcript_time, finished)
