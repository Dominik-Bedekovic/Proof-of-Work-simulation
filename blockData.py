import utils
import datetime


class BlockData:

    # Generate a random hash representing the hash of the previous block.
    previous_hash = utils.create_hash(utils.random_string(20))

    # Store the current timestamp as the creation time of the block.
    timestamp = str(datetime.datetime.now())

    # Generate a collection of random transactions for the block.
    transactions = utils.random_transactions()