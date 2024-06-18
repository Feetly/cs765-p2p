import numpy as np
# Initialize a random number generator with a specific seed
rng = np.random.default_rng(69)

# Initialize a random number generator with a specific seed

blk_create_ctr = 0
def blk_incre():
    """
    Increment the block creation counter.
    """
    globals()['blk_create_ctr'] += 1

def get_blks():
    """
    Get the current value of the block creation counter.

    Returns:
        int: The current value of the block creation counter.
    """
    return globals()['blk_create_ctr']