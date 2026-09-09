"""Execute PoW batches and maintain nonce state at the simulated stopping time."""

from blockFunctions import BlockFunctions


def pow_worker(args):
    """Try up to one simulated second of hashes; return success or the next-attempt
    state.
    """
    (
        nonce,
        extra_nonce,
        reward,
        merkle_root,
        hash_rate,
        previous_hash,
        timestamp,
        difficulty,
        transactions,
    ) = args
    for i in range(hash_rate):
        header_hash = BlockFunctions.create_header_hash(
            previous_hash, timestamp, merkle_root, nonce
        )

        # Difficulty counts hexadecimal leading zeroes in the SHA-256 digest.
        if header_hash.startswith("0" * difficulty):
            return {
                "found": True,
                "hashes": i + 1,
                "nonce": nonce,
                "extra_nonce": extra_nonce,
                "merkle_root": merkle_root,
                "header_hash": header_hash,
            }

        # Changing the extra nonce produces another header after the nonce space is exhausted.
        if nonce == 2**32 - 1:
            nonce = 0
            extra_nonce += 1
            coinbase = {"reward": reward, "extra_nonce": extra_nonce}
            merkle_root = BlockFunctions.calculate_merkle_root(transactions, coinbase)
        else:
            nonce += 1
    return {
        "found": False,
        "hashes": hash_rate,
        "nonce": nonce,
        "extra_nonce": extra_nonce,
        "merkle_root": merkle_root,
        "header_hash": None,
    }


def advance_state(node, completed_hashes):
    """Advance the next-attempt cursor, including nonce-space wraparound."""
    wraps, node.nonce = divmod(node.nonce + completed_hashes, 2**32)
    if wraps:
        node.coinbase["extra_nonce"] += wraps
        node.merkle_root = BlockFunctions.calculate_merkle_root(
            node.blockData.transactions, node.coinbase
        )
