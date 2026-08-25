import utils

class BlockFunctions:

    @staticmethod
    def calculate_merkle_root(block_transactions, node_coinbase):
    
            transaction_string = ''
            for transaction in block_transactions:
                transaction_string += str(transaction)  
            #print("Transaction string: " + transaction_string)
    
            coinbase_string = ''
            for value in node_coinbase.values():
                coinbase_string += str(value) 
            #print("Coinbase string: " + coinbase_string)
    
            merkle_root = transaction_string + coinbase_string
    
            return utils.create_hash(merkle_root)

    @staticmethod
    def create_header_hash(block_prev_hash, block_timestamp, merkle_root, node_nonce):
        #print("block previous hash:" + self.blockData.previous_hash)
        #print("timestamp: " + str(self.blockData.timestamp))
        #print("merkle root hash: " + self.merkle_root)
            
        data = (block_prev_hash + block_timestamp
                    + merkle_root + str(node_nonce))
    
        return utils.create_hash(data)