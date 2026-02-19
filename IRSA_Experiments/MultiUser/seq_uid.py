import numpy as np
from gnuradio import gr
import pmt
import time

class blk(gr.sync_block):

    def __init__(self, user_id=0, samp_rate=768000, packet_samples=100000):
        gr.sync_block.__init__(
            self,
            name="seq_tagger",
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )
        self.user_id         = user_id
        self.samp_rate       = samp_rate
        self.packet_samples  = packet_samples
        self.seq_num         = 0
        self.last_tag_offset = None
        self.set_tag_propagation_policy(gr.TPP_ALL_TO_ALL)

    def work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]
        out[:] = inp

        # ── Use pmt.intern() directly, NOT self.pmt_intern() ──
        tags = self.get_tags_in_window(
            0, 0, len(inp),
            pmt.intern("packet_len")   # ← pmt.intern not self.pmt_intern
        )

        for tag in tags:
            offset  = tag.offset

            # Measure actual packet samples between tags
            if self.last_tag_offset is not None:
                measured = offset - self.last_tag_offset
                print(f"[User {self.user_id}] "
                      f"Measured packet_samples = {measured}")
            self.last_tag_offset = offset

            self.seq_num += 1

            # Add user_id tag
            self.add_item_tag(
                0, offset,
                pmt.intern("user_id"),         # ← pmt.intern
                pmt.from_long(self.user_id)    # ← pmt.from_long
            )

            # Add sequence number tag
            self.add_item_tag(
                0, offset,
                pmt.intern("seq_num"),
                pmt.from_long(self.seq_num)
            )

            # Add timestamp tag
            self.add_item_tag(
                0, offset,
                pmt.intern("tx_time"),
                pmt.from_double(time.time())   # ← pmt.from_double
            )

            print(f"[User {self.user_id}] Tagged PKT "
                  f"seq={self.seq_num} offset={offset}")

        return len(inp)