from blockData import BlockData
from blockFunctions import BlockFunctions
from tspData import TspData
from tspFunctions import TspFunction
import utils


class Node:

    blockData = BlockData()
    simulation_time = 0
    found = False
    tsp = None

    @classmethod
    def initialize_tsp(cls, num_of_nodes):
        cls.tsp = TspData(num_of_nodes)

    def __init__(self, name):

        self.name = name

        self.coinbase = {
            "reward": utils.random_string(10),
            "extra_nonce": 0
        }

        self.merkle_root = BlockFunctions.calculate_merkle_root(self.blockData.transactions, self.coinbase)

        self.nonce = 0

        self.hash_rate = utils.random_num(50, 200)

        self.mining_count = 1

    def pow_mining(self, leading_zeros):

        self.zero_count = int(leading_zeros)

        for _ in range(self.hash_rate):

            self.header_hash = BlockFunctions.create_header_hash(self.blockData.previous_hash, 
                self.blockData.timestamp, self.merkle_root, self.nonce)
            
            #print(f"Header hash: {self.mining_count}: {self.header_hash}")

            if self.header_hash.startswith("0" * self.zero_count):
                return {
                        "node": self,
                        "name": self.name,
                        "hashes": self.mining_count,
                        "time": Node.simulation_time,
                        "exact time": self.mining_count / self.hash_rate,
                        "hash": self.header_hash
                        }
            
            elif self.nonce == pow(2, 32) - 1:
                self.coinbase["extra_nonce"] += 1
                self.merkle_root = BlockFunctions.calculate_merkle_root(self.blockData.transactions, self.coinbase)
                self.nonce = 0

            else:
                self.mining_count += 1
                self.nonce += 1

        return None

    def pouw_mining(self):
        best_cost, best_path = TspFunction.tsp_solver(self.tsp)

        return best_cost, best_path
            

