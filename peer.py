from helper import blk_incre, rng
from transaction import Transaction
from block import Block
from collections import deque
import networkx as nx
from handler import Handler, enqueue

def compute_linkLatency(sender, receiver, txn_size = 1):
    """
    Compute the link latency between two peers.

    Args:
        sender (Peer): The sending peer.
        receiver (Peer): The receiving peer.
        txn_size (int): Size of the transaction.

    Returns:
        float: The computed link latency.
    """
    latency = rng.uniform(10, 500, 1)
    bandwidth = 5 if sender.is_slow or receiver.is_slow else 100
    delay = rng.exponential(96 / bandwidth)
    return latency + (txn_size/bandwidth) + delay

def verify_block(block):
    """
    Verify the integrity of a block.

    Args:
        block (Block): The block to be verified.

    Returns:
        bool: True if the block is valid, False otherwise.
    """
    for txn in block.txn_in_blk:
        if not txn.coinbase:
            if not (block.balance[txn.sender.peer_id] ==  block.parent_blk.balance[txn.sender.peer_id] - txn.coins and
            block.balance[txn.receiver.peer_id] == block.parent_blk.balance[txn.receiver.peer_id] + txn.coins and
            block.balance[txn.sender.peer_id] < 0): return False
    return True

class Peer:
    """
        Initialize a Peer instance.

        Args:
            is_slow (bool): Flag indicating if the peer is slow.
            is_low_cpu (bool): Flag indicating if the peer has low CPU.
            genesis (Block): The genesis block.
            miningTime (float): Average inter-arrival time/hashpower.
        """
    peer_ctr = 0
    def __init__(self, is_slow, is_low_cpu, genesis, miningTime,):
        self.peer_id = Peer.peer_ctr
        Peer.peer_ctr += 1
        self.is_slow = is_slow
        self.is_low_cpu = is_low_cpu
        self.connected_peers = set() # neighbours of the node
        self.txnReceived = set() # txn received till now 

        self.blockChain = dict() # blockchain of the node
        self.blockReceived = set() # blocks received till now 
        self.blockTime = dict() # time at which each block arrived
        self.orphanBlocks = set() # blocks received whose parents have not been received yet
        self.blockTime[1] = 0
        self.g = nx.DiGraph() # graph
        
        self.last_blk_id = genesis.blk_id
        self.blockChain[self.last_blk_id] = genesis
        self.miningTime = miningTime # avg interarrival time/hashpower
        self.created_blocks_own = 0

    def connect_to_peers(self, peer_objects, edges):
        """
        Connect to peer nodes.

        Args:
            peer_objects (list): List of Peer objects.
            edges (list): List of edges representing connections.
        """
        connected_nodes = set()
        for edge in edges:
            if edge[0] == self.peer_id:
                connected_nodes.add(edge[1])
            elif edge[1] == self.peer_id:
                connected_nodes.add(edge[0])

        # Convert connected node IDs to corresponding Peer objects
        connected_peers = []
        for node_id in connected_nodes:
            for peer in peer_objects:
                if peer.peer_id == node_id:
                    connected_peers.append(peer)

        self.connected_peers = connected_peers

    def broadcast_txn(self, handler):
        """
        Broadcast a transaction to connected peers.

        Args:
            handler (Handler): Handler object containing transaction information.
        """
        for neighbour in self.connected_peers:
            new_time = handler.time_occured + compute_linkLatency(self, neighbour)
            enqueue(Handler("TxnRecv", new_time, self.peer_id, neighbour, handler.txn))

    # generates transactions
    def txnSend(self, handler):
        """
        Send a transaction to connected peers.

        Args:
            handler (Handler): Handler object containing transaction information.
        """
        curr_bal = self.blockChain[self.last_blk_id].balance[self.peer_id]
        handler.txn.coins = rng.integers(1, curr_bal)
        self.txnReceived.add(handler.txn)
        self.broadcast_txn(handler)

    # forwards transactions
    def txnRecv(self, handler):
        """
        Receive and forward transactions.

        Args:
            handler (Handler): Handler object containing transaction information.
        """
        if handler.txn not in self.txnReceived:
            self.txnReceived.add(handler.txn)
            self.broadcast_txn(handler)

    # new block generation
    def mineNewBlock(self, block, lat):
        """
        Mine a new block.

        Args:
            block (Block): The block to be mined.
            lat (float): Latency.
        """
        while True:
            remaingTxn = self.txnReceived.difference(block.txn_mem_pool)
            toBeDeleted = set([i for i in remaingTxn if i.coins > block.balance[i.sender.peer_id]])
            remaingTxn = remaingTxn.difference(toBeDeleted)
            numTxn = len(remaingTxn)
            
            if numTxn > 1:
                numTxn = min(rng.integers(1, numTxn), 1022) # 1 for coinbase txn, 1 for itself

            txnToInclude = set(rng.choice(list(remaingTxn), numTxn))
            coinBaseTxn = Transaction(self, self, 50, True)
            txnToInclude.add(coinBaseTxn)

            newBlock = Block(self, block, txnToInclude)
            if verify_block(newBlock): break

        lat = lat + rng.exponential(self.miningTime) #takes mean not lambda
        enqueue(Handler("BlockMined", lat, blk=newBlock))


    #this function is called, if block receives a node from its peers
    #block is verified and if the block is without any errors then its is added to blockchain 
    # and then transmitted to neighbours 
    # If addition of that block creates a primary chain then mining is started over that block
    def verifyAndAddReceivedBlock(self, handler):
        """
        Verify and add received block to blockchain.

        Args:
            handler (Handler): Handler object containing block information.
        """
        if handler.blk.blk_id not in self.blockReceived:
            self.blockReceived.add(handler.blk.blk_id)
            if not verify_block(handler.blk):
                return
            if handler.blk.parent_blk.blk_id not in self.blockChain:
                self.orphanBlocks.add(handler.blk)
                return

            orphan_processing_queue = deque([handler.blk])
            last_block_in_chain = handler.blk

            while orphan_processing_queue:
                current_block = orphan_processing_queue.popleft()
                self.blockTime[current_block.blk_id] = handler.time_occured
                self.blockChain[current_block.blk_id] = current_block
                self.g.add_edge(current_block.blk_id, current_block.parent_blk.blk_id)

                if current_block.chain_length > last_block_in_chain.chain_length:
                    last_block_in_chain = current_block

                for peer in self.connected_peers:
                    latency = handler.time_occured + compute_linkLatency(self, peer, current_block.size)
                    enqueue(Handler("BlockRecv", latency, sender=self, receiver=peer, blk=current_block))

                for orphan_block in list(self.orphanBlocks):
                    if orphan_block.parent_blk.blk_id == current_block.blk_id:
                        self.orphanBlocks.remove(orphan_block)
                        orphan_processing_queue.append(orphan_block)

            if last_block_in_chain.chain_length > self.blockChain[self.last_blk_id].chain_length:
                self.last_blk_id = last_block_in_chain.blk_id
                self.mineNewBlock(block=last_block_in_chain, lat=handler.time_occured)

        
    # this function is called once the mining of a block is completed, 
    # If after mining the addition of block creates a primary chain then
    # the block is shared with neighbours and mining is continued otherwise 
    # node waits a block whose addition will, create primary chain
    def receiveSelfMinedBlock(self, handler):
        """
        Receive a self-mined block.

        Args:
            handler (Handler): Handler object containing block information.
        """
        if handler.blk.chain_length <= self.blockChain[self.last_blk_id].chain_length:
            return

        blk_incre()
        self.created_blocks_own += 1
        self.blockTime[handler.blk.blk_id] = handler.time_occured
        self.blockChain[handler.blk.blk_id] = handler.blk
        self.g.add_edge(handler.blk.blk_id, handler.blk.parent_blk.blk_id)
        self.blockReceived.add(handler.blk.blk_id)

        for peer in self.connected_peers:
            latency = handler.time_occured + compute_linkLatency(self, peer, handler.blk.size)
            enqueue(Handler("BlockRecv", latency, sender=self, receiver=peer, blk=handler.blk))

        self.mineNewBlock(block=handler.blk, lat=handler.time_occured)
