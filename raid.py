#!/usr/bin/env python
"""Simple demonstration of RAID5

This demonstrates a very rudimentary implementation of RAID5 and its relevant
objects and methods.  It is meant to be illustrative, not useful.
"""

class Raid5Stripe(object):
    """Rudimentary RAID 5 stripe
    """
    def __init__(self, width):
        """Initialize the RAID stripe

        Initialize a RAID stripe and all of its blocks.  The block size is
        currently statically defined as having the size of a Python long int;
        the stripe width is user-defined.

        Args:
            width (int): The number of data blocks to be used in this stripe
        """
        self.width = width
        self.blocks = [0L] * width
        self.parity = self.calculate_parity()

    def write(self, block_id, contents):
        """Change the contents of a RAID block

        Args:
            block_id (int): the index of the block to be rewritten
            contents (binary): the new contents to be written to the block being
                rewritten
        """
        old_block = self.blocks[block_id]

        parity = self.calculate_parity(old_block=old_block, new_block=contents)
        self.blocks[block_id] = contents
        self.parity = parity

    def read(self, block_id):
        """Read a block and verify its parity

        On error, raise an exception because the stripe cannot determine if the
        parity or the data block is what is corrupted.  A higher-level structure
        will have to make this determination by correlating corrupt blocks to a
        RAID device.

        Args:
            block_id (int): the index of the block to be read
        """
        calculated_block = self.calculate_block(block_id)
        if calculated_block != self.blocks[block_id]:
            raise IOError("Corruption detected in either parity block or data block")
        else:
            return calculated_block

    def fast_read(self, block_id):
        """Read a block without verifying its parity

        Args:
            block_id (int): the index of the block to be read
        """
        return self.blocks[block_id]

    def calculate_block(self, block_id):
        """Recalculate a data block based on other blocks and the parity block

        This does not modify the state of the parent object.

        Args:
            block_id (int): the index of the block to be recalculated from
                parity

        Returns:
            binary: The contents of the recalculated data block
        """
        calculated_block = None
        for block in self.blocks[0:block_id] + self.blocks[block_id+1:]:
            if calculated_block is not None:
                calculated_block ^= block
            else:
                calculated_block = block

        return calculated_block ^ self.parity

    def calculate_parity(self, old_block=None, new_block=None):
        """Calculate parity for the stripe

        Calculates the parity for the stripe.  If old_block and new_block are
        defined, don't recalculate parity using the whole stripe; instead use
        the associativity and commutivity of XOR to calculate the new parity
        based only on the block that is being altered.

        Does NOT change the state of the parent object; simply returns the
        parity.

        Args:
            old_block (binary): data contained in a block that will be updated
            new_block (binary): data to replace the old_block data

        Returns:
            binary: parity block
        """
        if old_block is not None and new_block is not None:
            parity = old_block ^ new_block ^ self.parity
        else:
            parity = self.blocks[0]
            for block in self.blocks[1:]:
                parity ^= block
        return parity

def test_rebuild_stripe(reference_blocks=None, width=8):
    """Ensure that parity is rebuilt correctly

    Args:
        reference_blocks (list of 8-bit ints or None): Blocks to use for raid
            stripe
        width (int): Number of blocks to randomly generate if reference_blocks
            is None.  Otherwise ignored.
    """

    if reference_blocks is None:
        import random
        random.seed(a=0)
        stripe = Raid5Stripe(width=width)
        reference_blocks = [random.randint(0, 0b11111111) for x in range(width)]

    # Set contents of each block in the RAID stripe
    print "                     parity is {:08b}".format(stripe.parity)
    for block_id, contents in enumerate(reference_blocks):
        stripe.write(block_id=block_id, contents=contents)
        print "Added {:08b} at %d; parity is {:08b}".format(stripe.blocks[block_id], stripe.parity) % block_id

    # Recalculate every block based on parity
    for missing in range(stripe.width):
        print_str = ""
        for blockid in range(stripe.width):
            if blockid == missing:
                print_str += "???????? "
            else:
                print_str += "{:08b} ".format(stripe.blocks[blockid])
        calculated_block = stripe.calculate_block(missing)
        print print_str
        print "parity:     {:08b}".format(stripe.parity)
        print "calculated: {:08b}".format(calculated_block)
        print "vs          {:08b}".format(stripe.blocks[missing])
        assert calculated_block == stripe.blocks[missing]

if __name__ == "__main__":
    test_rebuild_stripe()
