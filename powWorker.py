from blockFunctions import BlockFunctions


def pow_worker(args):
    # Unpack the current mining state of the node.
    (
        nonce,
        extra_nonce,
        reward,
        merkle_root,
        hash_rate,
        previous_hash,
        timestamp,
        difficulty,
        transactions
    ) = args

    # Perform the number of hash attempts defined by the node's hash rate.
    for i in range(hash_rate):
        # Create a hash from the current block header.
        header_hash = BlockFunctions.create_header_hash(
            previous_hash,
            timestamp,
            merkle_root,
            nonce
        )

        # Check whether the hash meets the required difficulty.
        if header_hash.startswith("0" * difficulty):
            # Return the mining state when a valid hash is found.
            return {
                "found": True,
                "hashes": i + 1,
                "nonce": nonce,
                "extra_nonce": extra_nonce,
                "merkle_root": merkle_root,
                "header_hash": header_hash
            }

        # Check whether the 32-bit nonce space has been exhausted.
        if nonce == (2 ** 32) - 1:
            nonce = 0
            extra_nonce += 1

            # Changing the extra nonce changes the coinbase data
            # and therefore the Merkle root.
            coinbase = {
                "reward": reward,
                "extra_nonce": extra_nonce
            }

            merkle_root = BlockFunctions.calculate_merkle_root(
                transactions,
                coinbase
            )
        else:
            # Move to the next nonce for the next hash attempt.
            nonce += 1

    # Return the updated mining state if no valid hash was found.
    return {
        "found": False,
        "hashes": hash_rate,
        "nonce": nonce,
        "extra_nonce": extra_nonce,
        "merkle_root": merkle_root,
        "header_hash": None
    }