import heapq

class Handler:
    """
    Represents an event handler for managing events in the simulation.

    Attributes:
        type (str): The type of event.
        time_occurred (float): The time at which the event occurred.
        txn (Transaction): The transaction associated with the event.
        blk (Block): The block associated with the event.
        sender (Peer): The sender peer associated with the event.
        receiver (Peer): The receiver peer associated with the event.
    """
    def __init__(self, type, time_occured, sender=None, receiver=None, txn=None, blk=None):
        """
        Initialize a Handler instance.

        Args:
            type (str): The type of event.
            time_occurred (float): The time at which the event occurred.
            sender (Peer): The sender peer associated with the event. Default is None.
            receiver (Peer): The receiver peer associated with the event. Default is None.
            txn (Transaction): The transaction associated with the event. Default is None.
            blk (Block): The block associated with the event. Default is None.
        """
        self.type = type
        self.time_occured = time_occured
        self.txn = txn
        self.blk = blk
        self.sender = sender
        self.receiver = receiver

def enqueue(handler):
    """
    Enqueue a handler into the event handler queue.

    Args:
        handler (Handler): The handler to be enqueued.
    """
    heapq.heappush(handler_queue, (handler.time_occured, handler))

handler_queue = []