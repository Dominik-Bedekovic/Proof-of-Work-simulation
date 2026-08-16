from nodes import Node
from tspData import TspData
from tspFunctions import TspFunction

#example = BlockData()
#example2 = BlockData()

Node.initialize_tsp(4)

node1 = Node()
node2 = Node()
node3 = Node()

#print(node1.tsp is node2.tsp)

#child = TspFunction.create_child(tsp_root, tsp.matrix, tsp_root.vertex, 1)
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

#print(node1.pow_mining(4))

#print(tsp.matrix)
#print(TspFunction.matrix_reduction(tsp.matrix))
#print(tsp.cost, tsp.reduced_matrix)
#print("parent matrix: " + str(tsp_root.matrix))
#print("parent cost: " + str(tsp_root.cost))
#print("child matrix: " + str(child.matrix))
#print("child path: " + str(child.path))
#print("child cost: " + str(child.cost))
#print("child vertex: " + str(child.vertex))
print(node1.tsp.matrix)
print(node1.pow_mining(4))
print(node1.pouw_mining())