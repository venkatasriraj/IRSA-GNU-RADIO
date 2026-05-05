import numpy as np
from gnuradio import gr
import pmt
import time

class blk(gr.sync_block):
    def __init__(self, user_id=1, samp_rate=32000): # Updated default samp_rate to match your Tx
        gr.sync_block.__init__(
            self,
            name="seq_tagger",
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )
        self.user_id = user_id
        self.samp_rate = samp_rate
        self.last_tag_offset = None
        # Ensure tags (like burst_start) pass through this block
        self.set_tag_propagation_policy(gr.TPP_ALL_TO_ALL)

    def work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]
        out[:] = inp

        # Search for 'burst_start' instead of 'packet_len'
        tags = self.get_tags_in_window(
            0, 0, len(inp),
            pmt.intern("burst_start")
        )

        for tag in tags:
            offset = tag.offset
            now = time.time()
            
            # Add a timestamp tag for logging/latency calculations
            self.add_item_tag(
                0, offset,
                pmt.intern("tx_time"),
                pmt.from_double(now)
            )
            
            # Diagnostic print to the console
            print(f"[seq_tagger TX{self.user_id}] Burst detected at offset {offset}. TS: {now:.6f}")

        return len(inp)