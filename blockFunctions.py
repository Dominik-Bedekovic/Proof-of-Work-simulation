import utils


class BlockFunctions:

    @staticmethod
    def calculate_merkle_root(block_transactions, node_coinbase):
        # Combine all block transactions into one string.
        transaction_string = ''

        for transaction in block_transactions:
            transaction_string += str(transaction)

        # Combine the values of the coinbase transaction into one string.
        coinbase_string = ''

        for value in node_coinbase.values():
            coinbase_string += str(value)

        # Combine the transaction and coinbase data.
        merkle_root = transaction_string + coinbase_string

        # Hash the combined data to create the Merkle root.
        return utils.create_hash(merkle_root)

    @staticmethod
    def create_header_hash(
        block_prev_hash,
        block_timestamp,
        merkle_root,
        node_nonce
    ):
        # Combine the block header fields into one string.
        data = (
            block_prev_hash
            + block_timestamp
            + merkle_root
            + str(node_nonce)
        )

        # Hash the block header using SHA-256.
        return utils.create_hash(data)