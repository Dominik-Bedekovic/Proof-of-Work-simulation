from blockFunctions import BlockFunctions


def pow_worker(args):

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

    for i in range(hash_rate):

        header_hash = BlockFunctions.create_header_hash(
            previous_hash,
            timestamp,
            merkle_root,
            nonce
        )

        # Valid hash found.
        if header_hash.startswith("0" * difficulty):

            return {
                "found": True,
                "hashes": i + 1,
                "nonce": nonce,
                "extra_nonce": extra_nonce,
                "merkle_root": merkle_root,
                "header_hash": header_hash
            }

        # 32-bit nonce exhausted.
        if nonce == (2 ** 32) - 1:

            nonce = 0
            extra_nonce += 1

            coinbase = {
                "reward": reward,
                "extra_nonce": extra_nonce
            }

            merkle_root = BlockFunctions.calculate_merkle_root(
                transactions,
                coinbase
            )

        else:
            nonce += 1

    return {
        "found": False,
        "hashes": hash_rate,
        "nonce": nonce,
        "extra_nonce": extra_nonce,
        "merkle_root": merkle_root,
        "header_hash": None
    }