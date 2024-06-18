class Block:
    blk_ctr = 2
    def __init__(self, miner, parent_blk, txn_in_blk=set(), balance=[]):
        """
        Initialize a Block instance.

        Args:
            miner (Peer): The peer that mined this block.
            parent_blk (Block or int): The parent block of this block.
            txn_in_blk (set): Set of transactions included in the block.
            balance (list): List representing the balance of each peer in the blockchain network.
        """
        if parent_blk == 0 :
            # Genesis block initialization
            self.blk_id = 1
            self.txn_in_blk = set()
            self.txn_mem_pool = set()
            self.chain_length = 1
            self.balance = balance
        else :
            # Regular block initialization
            self.blk_id = Block.blk_ctr
            Block.blk_ctr += 1
            self.txn_in_blk = txn_in_blk
            self.txn_mem_pool = parent_blk.txn_mem_pool
            self.chain_length = parent_blk.chain_length + 1
            self.balance = parent_blk.balance.copy()

        self.parent_blk = parent_blk
        self.size = 1 + len(txn_in_blk)
        self.miner = miner
        # Update balance based on transactions in the block
        for txns in txn_in_blk:
            if not txns.coinbase:
                self.balance[txns.sender.peer_id] -= txns.coins
            self.balance[txns.receiver.peer_id] += txns.coins
            self.txn_mem_pool.add(txns)