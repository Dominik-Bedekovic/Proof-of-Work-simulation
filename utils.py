import hashlib
import random
import string

inf = float("inf")

def random_string(char_num):

    return ''.join(random.choices(string.ascii_letters + string.digits, k=char_num))

def create_hash(hash_BlockData):

    return hashlib.sha256(hash_BlockData.encode()).hexdigest()

def random_num(min_num, max_num):

    random_num = random.randint(min_num, max_num)

    return random_num

def random_transactions():

    transactions = list()
    num_of_elements = random_num(5, 20) 

    while num_of_elements > 0:
        num_of_elements -= 1
        transactions.append(random_string(10))

    return tuple(transactions)