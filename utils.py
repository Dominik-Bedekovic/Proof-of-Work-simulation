import hashlib
import random
import string

def random_string(char_num):

    return ''.join(random.choices(string.ascii_letters + string.digits, k=char_num))

def create_hash(hash_BlockData):

    return hashlib.sha256(hash_BlockData.encode()).hexdigest()

def random_transactions():

    min_transactions = 5
    max_transactions = 20
    elements = random.randint(min_transactions, max_transactions)

    transactions = list()
    while elements > 0:
        elements -= 1
        transactions.append(random_string(10))

    return tuple(transactions)

