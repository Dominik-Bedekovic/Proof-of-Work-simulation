from blockData import BlockData
from blockFunctions import BlockFunctions
import utils


class Node:

    blockData = BlockData()

    def __init__(self):

        self.coinbase = {
            "reward": utils.random_string(10),
            "extra_nonce": 0
        }

        self.merkle_root = BlockFunctions.calculate_merkle_root(self.blockData.transactions, self.coinbase)

        self.nonce = 0

    def pow_mining(self, leading_zeros):

        self.mining_count = 1
        self.zero_count = int(leading_zeros)
        while True:

            self.header_hash = BlockFunctions.create_header_hash(self.blockData.previous_hash, 
                self.blockData.timestamp, self.merkle_root, self.nonce)
            
            print(f"Header hash: {self.mining_count}: {self.header_hash}")

            if self.header_hash.startswith("0" * self.zero_count):
                return ("You win!" + " " + "Mining count: " + str(self.mining_count))
            
            elif self.nonce == pow(2, 32) - 1:
                self.coinbase["extra_nonce"] += 1
                self.merkle_root = BlockFunctions.calculate_merkle_root(self.blockData.transactions, self.coinbase)
                self.nonce = 0

            else:
                self.mining_count += 1
                self.nonce += 1
    