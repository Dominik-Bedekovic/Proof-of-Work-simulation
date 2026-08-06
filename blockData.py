import utils
import datetime

class BlockData:
    previous_hash = utils.create_hash(utils.random_string(20))
    timestamp = str(datetime.datetime.now())
    transactions = utils.random_transactions()

