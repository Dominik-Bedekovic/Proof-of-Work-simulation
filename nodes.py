from blockData import BlockData
from blockFunctions import BlockFunctions
from tspData import TspData
from tspFunctions import TspFunction
from transcript import Transcript
import utils

class Node:

    # BlockData is shared between all nodes because every node
    # must attempt to mine the same block.
    blockData = BlockData()

    # Global simulation time shared by all nodes.
    simulation_time = 0

    # Indicates whether a solution has been found.
    found = False

    # Shared TSP problem used by all PoUW nodes.
    tsp = None
    transcript = None

    @classmethod
    def initialize_tsp(cls, num_of_nodes):
        # Generate the shared TSP problem used during the PoUW simulation.
        cls.tsp = TspData(num_of_nodes)
    @classmethod
    def initialize_transcript(cls):
        cls.transcript = Transcript()

    def __init__(self, name):
        # Identifier used to distinguish individual nodes.
        self.name = name

        # Generate node-specific coinbase data.
        # The extra nonce allows additional nonce values to be explored
        # once the standard 32-bit nonce range has been exhausted.
        self.coinbase = {
            "reward": utils.random_string(10),
            "extra_nonce": 0
        }

        # Generate the Merkle root from the shared block transactions
        # and the node-specific coinbase data.
        self.merkle_root = BlockFunctions.calculate_merkle_root(
            self.blockData.transactions,
            self.coinbase
        )

        # Initial nonce value used during PoW mining.
        self.nonce = 0

        # Simulated number of hash operations the node can perform
        # during one simulation step.
        self.hash_rate = utils.random_num(100, 1000)

        # Total number of hash operations performed by the node.
        self.mining_count = 0

        # Calculate the corresponding PoUW search rate using the
        # measured ratio between PoW and PoUW computational rates.
        ratio = getattr(Node, "pouw_pow_ratio", 1)
        self.search_rate = round(self.hash_rate * ratio)

        validation_ratio = getattr(Node, "validation_pow_ratio", 0)
        self.validation_rate = round(self.hash_rate * validation_ratio)

        # Calculate the corresponding transcript rate.
        transcript_ratio = getattr(
            Node,
            "transcript_pouw_ratio",
            0
        )
        self.transcript_rate = round(
            self.hash_rate * transcript_ratio
        )

        # Calculate the corresponding path validation rate.
        path_validation_ratio = getattr(
            Node,
            "path_validation_pow_ratio",
            0
        )
        self.path_validation_rate = round(
            self.hash_rate * path_validation_ratio
        )

        # Calculate the corresponding hash validation rate.
        hash_validation_ratio = getattr(
            Node,
            "hash_validation_pow_ratio",
            0
        )
        self.hash_validation_rate = round(
            self.hash_rate * hash_validation_ratio
        )



        # Total number of TSP search-node computations performed
        # by this node.
        self.computations = 0
        self.work = 0.0

    def update_pow_state(self, result):
        self.mining_count += result["hashes"]

        self.nonce = result["nonce"]

        self.coinbase["extra_nonce"] = result["extra_nonce"]

        self.merkle_root = result["merkle_root"]

        if result["found"]:
            self.header_hash = result["header_hash"]

    def pouw_mining(self):
        # Process a batch of TSP search-tree nodes according to the
        # simulated search rate of this node.

        transcript = (Node.transcript)
        temp_computation, work, transcript_time, finished = TspFunction.tsp_solver(
            self.tsp,
            self.search_rate,
            transcript,
            Node.transcript_pouw_ratio
        )

        # Add the number of processed search nodes to the node's
        # total computational work.
        self.work += work
        self.computations += work

        # Return the number of computations performed and indicate
        # whether the shared TSP search has been completed.
        return temp_computation, self.work, transcript_time, finished