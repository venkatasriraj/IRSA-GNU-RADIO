import numpy as np
import pmt
from gnuradio import gr

class nonblocking_add(gr.basic_block):
    """
    Drop-in replacement for the Add block in the channel flowgraph.
    Uses gr.basic_block + forecast(0) so it never stalls waiting
    for a bursty input. Whichever TX stream has no samples gets
    zero-substituted for that work() call.
    """
    def __init__(self, vlen=1):
        gr.basic_block.__init__(self,
            name="nonblocking_add",
            in_sig=[np.complex64, np.complex64],
            out_sig=[np.complex64])
        self.vlen = vlen

    def forecast(self, noutput_items, ninput_items_required):
        # *** KEY: declare 0 required from both inputs ***
        # The scheduler will NOT block waiting for either stream.
        # We handle the "nothing available" case in general_work.
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = 0

    def general_work(self, input_items, output_items):
        avail0 = len(input_items[0])   # samples available from TX1
        avail1 = len(input_items[1])   # samples available from TX2
        n_out  = len(output_items[0])  # space in output buffer

        # How many samples can we produce this call?
        # Take as many as the richer stream offers, capped by output space.
        # If both are empty we produce nothing — scheduler will retry.
        n = min(n_out, max(avail0, avail1))
        if n == 0:
            return 0   # both streams idle; yield back to scheduler

        # Build TX1 contribution
        if avail0 >= n:
            sig0 = np.array(input_items[0][:n], dtype=np.complex64)
            self.consume(0, n)
        elif avail0 > 0:
            # Partial data from TX1 — pad the rest with zeros
            sig0 = np.zeros(n, dtype=np.complex64)
            sig0[:avail0] = input_items[0][:avail0]
            self.consume(0, avail0)
        else:
            # TX1 completely idle this call
            sig0 = np.zeros(n, dtype=np.complex64)
            # consume(0, 0) — nothing to consume

        # Build TX2 contribution
        if avail1 >= n:
            sig1 = np.array(input_items[1][:n], dtype=np.complex64)
            self.consume(1, n)
        elif avail1 > 0:
            sig1 = np.zeros(n, dtype=np.complex64)
            sig1[:avail1] = input_items[1][:avail1]
            self.consume(1, avail1)
        else:
            sig1 = np.zeros(n, dtype=np.complex64)

        output_items[0][:n] = sig0 + sig1
        return n
    
"""
## Wiring in GRC (Image 2 change)

Remove the existing `Add` block. Place `nonblocking_add` in its position:

Virtual Source (f_samp1) ──> iq_logger (badd1) ──┐
                                                   ├──> nonblocking_add ──> Throttle ──> iq_logger (Aadd) ──> ZMQ PUB
Virtual Source (f_samp2) ──> iq_logger (badd2) ──┘
"""

