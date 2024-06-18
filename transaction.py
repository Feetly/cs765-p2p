class Transaction:
    txn_ctr = 0
    def __init__(self, sender=-1, receiver=-1, coins=0, coinbase=False):
        """
        Initialize a Transaction instance.

        Args:
            sender (int): ID of the sender.
            receiver (int): ID of the receiver.
            coins (int): Number of coins involved in the transaction.
            coinbase (bool): Indicates if the transaction is a coinbase transaction.
        """
        self.txnId = Transaction.txn_ctr
        Transaction.txn_ctr += 1
        self.sender = sender
        self.receiver = receiver
        self.coins = coins
        self.coinbase = coinbase
        self.size = 1

    def __repr__(self):
        """
        Represent the Transaction object as a string.

        Returns:
            str: A string representation of the Transaction object.
        """
        if coinbase:
           return f'TxnID {self.txnId} : {self.receiver} mines {self.coins} coins'
        return f'TxnID {self.txnId} : {self.sender} pays {self.receiver} {self.coins} coins'