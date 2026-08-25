from blockData import BlockData
from blockFunctions import BlockFunctions
from tspData import TspData
from tspFunctions import TspFunction
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


    @classmethod
    def initialize_tsp(cls, num_of_nodes):
        # Generate the shared TSP problem used during the PoUW simulation.
        cls.tsp = TspData(num_of_nodes)


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
        self.hash_rate = utils.random_num(50, 200)

        # Total number of hash operations performed by the node.
        self.mining_count = 0

        # Calculate the corresponding PoUW search rate using the
        # measured ratio between PoW and PoUW computational rates.
        ratio = getattr(Node, "pouw_pow_ratio", 1)
        self.search_rate = round(self.hash_rate * ratio)

        # Total number of TSP search-node computations performed
        # by this node.
        self.computations = 0


    def pow_mining(self, leading_zeros):
        # Set the required number of leading zeros for a valid hash.
        # This represents the difficulty of the pow mining sim 
        self.zero_count = int(leading_zeros)

        # Perform a batch of hash attempts according to the node's
        # simulated hash rate.
        for _ in range(self.hash_rate):

            # Mining count is used to track each node's work output
            # through incrementing nonce
            self.mining_count += 1

            # Generate a block header hash using the shared block data
            # and the node-specific Merkle root and nonce.
            self.header_hash = BlockFunctions.create_header_hash(
                self.blockData.previous_hash,
                self.blockData.timestamp,
                self.merkle_root,
                self.nonce
            )

            # Check whether the generated hash satisfies the
            # required difficulty.
            if self.header_hash.startswith("0" * self.zero_count):
                return self.mining_count

            # If the 32-bit nonce range is exhausted, reset the nonce
            # and increase the extra nonce to generate a new Merkle root.
            elif self.nonce == pow(2, 32) - 1:
                self.coinbase["extra_nonce"] += 1

                self.merkle_root = BlockFunctions.calculate_merkle_root(
                    self.blockData.transactions,
                    self.coinbase
                )

                self.nonce = 0

            # Otherwise, continue with the next nonce value.
            else:
                self.nonce += 1

        # No valid hash was found during this simulation step.
        return None


    def pouw_mining(self):
        # Process a batch of TSP search-tree nodes according to the
        # simulated search rate of this node.
        temp_computation, finished = TspFunction.tsp_solver(
            self.tsp,
            self.search_rate
        )

        # Add the number of processed search nodes to the node's
        # total computational work.
        self.computations += temp_computation

        # Return the number of computations performed and indicate
        # whether the shared TSP search has been completed.
        return temp_computation, finished