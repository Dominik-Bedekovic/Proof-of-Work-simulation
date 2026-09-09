"""Provide shared sample block-header inputs and transactions for the simulation."""

import utils
import datetime


class BlockData:
    """Shared sample block values, generated once when this class is defined."""

    # Class-level sample values are initialized once at import, not per BlockData instance.
    previous_hash = utils.create_hash(utils.random_string(20))
    timestamp = str(datetime.datetime.now())
    transactions = utils.random_transactions()
