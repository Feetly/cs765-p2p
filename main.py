import os
import heapq
import random
import shutil
import argparse
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

from transaction import Transaction
from block import Block
from peer import Peer
from helper import get_blks, rng
from handler import handler_queue, Handler


# Handle events 
def handle(event): #event handler 
    """
    Handle events based on their types.

    Args:
        event (Handler): The event to be handled.
    """
    if event.type == "TxnGen":
        event.txn.sender.txnSend(event)
    elif event.type == "TxnRecv":
        event.receiver.txnRecv(event)
    elif event.type == "BlockRecv":
        event.receiver.verifyAndAddReceivedBlock(event)
    elif event.type == "BlockMined":
        event.blk.miner.receiveSelfMinedBlock(event)

# plot
def visualize_blockchain(peer_id):
    """
    Visualize the blockchain of a peer and save the plot as an image.

    Args:
        peer_id (int): The ID of the peer.
    """
    plt.figure()
    # draw network with Kamada Kawai layout
    nx.draw(peers_net[peer_id].g, pos=nx.kamada_kawai_layout(peers_net[peer_id].g), node_size=10, node_color='red')
    plt.savefig(f'./figures/blockchain_{peer_id}.png')

# save plot
def print_graph(): #print graph     
    plt.figure()
    nx.draw(G, with_labels=True)
    plt.savefig('./figures/network_graph.png')

def print_network_stats():
    network_node = peers_net[0]
    genesis_block_id = 1

    reversed_graph = network_node.g.reverse()
    successors = nx.dfs_successors(reversed_graph, source=genesis_block_id)
    depth_map = {}
    max_depth_map = {}
    parent_map = {}
    deepest_node_id = genesis_block_id

    def depth_first_search(node_id, parent_id=None, depth=0):
        nonlocal deepest_node_id
        depth_map[node_id] = depth
        max_depth_map[node_id] = depth
        parent_map[node_id] = parent_id
        if depth > depth_map[deepest_node_id]:
            deepest_node_id = node_id
        if node_id not in successors:
            return
        for child_id in successors[node_id]:
            depth_first_search(child_id, node_id, depth + 1)
            max_depth_map[node_id] = max(max_depth_map[node_id], max_depth_map[child_id])

    depth_first_search(genesis_block_id)

    branch_lengths = []
    current_node = deepest_node_id
    while current_node != genesis_block_id:
        child_node = current_node
        current_node = parent_map[current_node]
        for sibling_id in successors.get(current_node, []):
            if sibling_id != child_node:
                branch_lengths.append(max_depth_map[sibling_id] - depth_map[current_node])

    # Initialize dictionaries to store statistics
    node_type_performance = {node_type: {'successful': 0, 'blocks_mined': 0} for node_type in ['slow_low', 'slow_high', 'fast_low', 'fast_high']}
    blocks_in_longest_chain = {peer.peer_id: 0 for peer in peers_net}

    # Aggregate statistics for each peer
    for peer in peers_net:
        peer_type = f"{'slow' if peer.is_slow else 'fast'}_{'low' if peer.is_low_cpu else 'high'}"
        node_type_performance[peer_type]['blocks_mined'] += peer.created_blocks_own

    block = network_node.blockChain[network_node.last_blk_id]
    while block.blk_id != genesis_block_id:
        blocks_in_longest_chain[block.miner.peer_id] += 1
        miner_type = f"{'slow' if block.miner.is_slow else 'fast'}_{'low' if block.miner.is_low_cpu else 'high'}"
        node_type_performance[miner_type]['successful'] += 1
        block = block.parent_blk

    # Print statistics
    print("Length of longest chain (including genesis block):", network_node.blockChain[network_node.last_blk_id].chain_length)
    print("Total number of blocks mined:", sum(peer.created_blocks_own for peer in peers_net))
    print("Fraction of mined blocks present in longest chain:", round((network_node.blockChain[network_node.last_blk_id].chain_length - 1) / sum(peer.created_blocks_own for peer in peers_net), 3))
    print()
    
    for node_type, stats in node_type_performance.items():
        if (network_node.blockChain[network_node.last_blk_id].chain_length - 1) > 0:
            print(f"% blocks in longest chain mined by {node_type} node:", round(stats['successful'] / (network_node.blockChain[network_node.last_blk_id].chain_length - 1), 2))
        else:
            print(f"% blocks in longest chain mined by {node_type} node: N/A")
    print()
    
    for node_type, stats in node_type_performance.items():
        if stats['blocks_mined'] > 0:
            print(f"% blocks mined by {node_type} node that made it to longest chain:", round(stats['successful'] / stats['blocks_mined'], 2))
        else:
            print(f"% blocks mined by {node_type} node that made it to longest chain: N/A")
    print()
    
    if branch_lengths:
        print("Lengths of branches:", branch_lengths)
        print("Average length of branch:", round(np.average(branch_lengths), 3))
    else:
        print("No branches were formed!")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initiate P2P Network")
    parser.add_argument("--n", type=int, default=15, help="Number of peers")
    parser.add_argument("--z0", type=float, default=10, help="Percentage of slow peers")
    parser.add_argument("--z1", type=float, default=40, help="Percentage of low CPU peers")
    parser.add_argument("--txn-mean", type=float, default=8, help="Interarrival time between transactions")
    args = parser.parse_args()
    # env = simpy.Environment()
    simulation_time=10000

    if os.path.exists('./logs'): shutil.rmtree('./logs')
    os.mkdir('./logs')

    if os.path.exists('./figures'): shutil.rmtree('./figures')
    os.mkdir('./figures')

    n, z0, z1, txn_mean = args.n, args.z0, args.z1, args.txn_mean

    G = nx.Graph()
    G.add_nodes_from(range(n))
    
    genesis_block = Block(parent_blk=0, txn_in_blk=set(), miner=None, balance=[1000]*n)    
    
    z0, z1 = z0/100.0, z1/100.0

    # genesis block
    genesis = Block(parent_blk = 0, miner=None, balance = [1000]*n)

    # CPU specs
    slow_selec = random.sample(range(n), int(z0*n))
    low_cpu_selec = random.sample(range(n), int(z1*n))

    # hashing power
    invh0 = n*(10 - 9*z1)
    invh1 = invh0/10
    I = 1000

    peers_net = []
    for i in range(n):
        is_slow = i in slow_selec
        is_low_cpu = i in low_cpu_selec
        miningTime = I*invh0 if is_slow else I*invh1
        p = Peer(is_slow = is_slow, is_low_cpu = is_low_cpu, genesis=genesis, miningTime=miningTime)
        peers_net.append(p)

    
    n = len(peers_net)
    graph = nx.connected_watts_strogatz_graph(n, k = random.randint(3, 6), p = 0.5)
    while not all(3 <= degree <= 6 for _, degree in graph.degree()):
        graph = nx.connected_watts_strogatz_graph(n, k = random.randint(3, 6), p = 0.5)
    
    for peer in peers_net:
        peer.connect_to_peers(peers_net, graph.edges()) 

    for e1, e2 in graph.edges():
        G.add_edge(e1, e2)   
    
    print_graph()

    for peer in peers_net:
        minetime = rng.exponential(peer.miningTime)
        block2mine = Block(miner = peer, parent_blk=genesis,txn_in_blk={Transaction(receiver=peer, coins=50, coinbase=True)})

        # adding block event to the queue
        heapq.heappush(handler_queue, (minetime, Handler("BlockMined", minetime, blk=block2mine)))
        
        # generate txn and add to the queue
        t = rng.exponential(txn_mean)
        while(t < simulation_time):
            elem = Transaction(sender = peer, receiver = peers_net[rng.integers(len(peers_net))])
            heapq.heappush(handler_queue, (t, Handler("TxnGen", t, txn=elem)))
            t = t + rng.exponential(txn_mean)

    time = 0
    while(time < simulation_time and len(handler_queue) > 0):
        time, event = heapq.heappop(handler_queue)
        handle(event)
    while(len(handler_queue) > 0):
        time, event = heapq.heappop(handler_queue)
        if event.type in ["TxnRecv", "BlockRecv"]:
            handle(event)


    for peer in peers_net: #each node
            file = open(f'./logs/log_tree_{peer.peer_id}.txt', 'w+') #store in file
            heading = f'Data For Node Id: {peer.peer_id}\n'
            file.write(heading)
            for _, block in peer.blockChain.items(): #each block
                parent, miner = None, None
                if block.parent_blk != 0: #if parent and miner exists
                    parent = block.parent_blk.blk_id
                    miner = block.miner.peer_id
                log_to_write = f"Block Id:{block.blk_id}, Parent ID:{parent}, Miner ID:{miner}, Txns:{len(block.txn_in_blk)}, Time:{peer.blockTime[block.blk_id]}\n"
                file.write(log_to_write)
            file.close()


    print_network_stats()

    for i in range(n):
        visualize_blockchain(i)