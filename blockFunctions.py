"""Construct the simplified transaction digest and block-header hashes."""

import utils


class BlockFunctions:
    """Hash the simplified transaction/coinbase data and block-header fields."""

    @staticmethod
    def calculate_merkle_root(block_transactions, node_coinbase):
        """Hash concatenated transactions and coinbase values; this is not a full
        Merkle tree.
        """
        transaction_string = ""
        for transaction in block_transactions:
            transaction_string += str(transaction)
        coinbase_string = ""
        for value in node_coinbase.values():
            coinbase_string += str(value)

        # This simplified digest is sufficient for distinct simulated mining inputs.
        merkle_root = transaction_string + coinbase_string
        return utils.create_hash(merkle_root)

    @staticmethod
    def create_header_hash(block_prev_hash, block_timestamp, merkle_root, node_nonce):
        """Return SHA-256 of the concatenated header fields and nonce."""
        data = block_prev_hash + block_timestamp + merkle_root + str(node_nonce)
        return utils.create_hash(data)
