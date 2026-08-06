from blockData import BlockData
import utils

class Node:

    blockData = BlockData()

    def __init__(self):

        self.coinbase = {
            "reward": utils.random_string(10),
            "extra_nonce": 0
        }

        self.merkle_root = self._calculate_merkle_root()

        self.nonce = 0

    def _calculate_merkle_root(self):

        transaction_string = ''
        for transaction in self.blockData.transactions:
            transaction_string += str(transaction)  
        #print("Transaction string: " + transaction_string)

        coinbase_string = ''
        for value in self.coinbase.values():
            coinbase_string += str(value) 
        #print("Coinbase string: " + coinbase_string)

        merkle_root = transaction_string + coinbase_string

        return utils.create_hash(merkle_root)

    def create_header_hash(self):
        #print("block previous hash:" + self.blockData.previous_hash)
        #print("timestamp: " + str(self.blockData.timestamp))
        #print("merkle root hash: " + self.merkle_root)
        
        data = (self.blockData.previous_hash + self.blockData.timestamp
                + self.merkle_root + str(self.nonce))

        return utils.create_hash(data)

    def pow_mining(self, leading_zeros):

        self.mining_count = 1
        self.zero_count = int(leading_zeros)
        while True:

            self.header_hash = self.create_header_hash()
            print(f"Header hash: {self.mining_count}: {self.header_hash}")

            if self.header_hash.startswith("0" * self.zero_count):
                return ("You win!" + " " + "Mining count: " + str(self.mining_count))
            
            elif self.nonce == pow(2, 32) - 1:
                self.coinbase["extra_nonce"] += 1
                self.merkle_root = self._calculate_merkle_root()
                self.nonce = 0

            else:
                self.mining_count += 1
                self.nonce += 1
