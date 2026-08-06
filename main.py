from blockData import BlockData
from nodes import Node

#example = BlockData()
#example2 = BlockData()

node1 = Node()



#print(node1.coinbase)
#print(node1.BlockData.transactions)
#print(node1.merkle_root)
#print(example.previous_hash)
#print(example.timestamp)
#print(example.previous_hash)
#print(example2.timestamp)
#print(example.transactions)
#print(example2.transactions)


#print(type(node1.coinbase))
#print(type(node1.BlockData.transactions))
#print(type(node1.merkle_root))
#print(type(BlockData.timestamp))
#print(type(BlockData.previous_hash))

print(node1.pow_mining(4))