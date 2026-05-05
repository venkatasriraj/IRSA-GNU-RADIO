import numpy as np
from gnuradio import gr
import pmt
import time

class blk(gr.sync_block):
    def __init__(self, user_id=0, samp_rate=48000):
        gr.sync_block.__init__(
            self,
            name="seq_tagger",
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )
        self.samp_rate       = samp_rate
        self.last_tag_offset = None
        self.set_tag_propagation_policy(gr.TPP_ALL_TO_ALL)

    def work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]
        out[:] = inp

        tags = self.get_tags_in_window(
            0, 0, len(inp),
            pmt.intern("packet_len")
        )

        for tag in tags:
            offset = tag.offset

            if self.last_tag_offset is not None:
                measured = offset - self.last_tag_offset
                # print(f"Measured packet_samples = {measured}")

            self.last_tag_offset = offset

            now = time.time()
            self.add_item_tag(
                0, offset,
                pmt.intern("rx_time"),
                pmt.from_double(now)
            )
            print(f"[seq_tagger] PKT offset={offset} rx_time={now:.6f}")

        return len(inp)