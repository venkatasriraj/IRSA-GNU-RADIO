import numpy as np
import random
import pmt
from gnuradio import gr

class stream_randomizer(gr.basic_block):
    def __init__(self, sample_rate=768000, mean_interval_ms=100.0):
        gr.basic_block.__init__(
            self,
            name="stream_randomizer",
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )
        self.sample_rate = sample_rate
        self.mean_interval_ms = mean_interval_ms

        self._pad_remaining = 0
        self._in_packet = False
        self._pkt_remaining = 0
        self._abs_offset = 0

        self.set_tag_propagation_policy(gr.TPP_DONT)

    def _draw_gap_samples(self):
        gap_ms = random.expovariate(1.0 / self.mean_interval_ms)
        return int(gap_ms * self.sample_rate / 1000.0)

    def general_work(self, input_items, output_items):   # ← general_work, not work
        in0 = input_items[0]
        out = output_items[0]
        nout = len(out)
        n_written = 0
        n_consumed = 0

        tags = self.get_tags_in_window(0, 0, len(in0), pmt.intern("packet_len"))

        while n_written < nout:
            if self._pad_remaining > 0:
                chunk = min(self._pad_remaining, nout - n_written)
                out[n_written:n_written + chunk] = 0 + 0j
                self._pad_remaining -= chunk
                n_written += chunk

            elif self._in_packet and self._pkt_remaining > 0:
                available = len(in0) - n_consumed
                chunk = min(self._pkt_remaining, nout - n_written, available)
                if chunk == 0:
                    break   # out of input — return what we have, called again next time
                out[n_written:n_written + chunk] = in0[n_consumed:n_consumed + chunk]
                self._pkt_remaining -= chunk
                n_written += chunk
                n_consumed += chunk
                if self._pkt_remaining == 0:
                    self._in_packet = False

            else:
                current_abs = self._abs_offset + n_consumed
                remaining_tags = [t for t in tags if t.offset >= current_abs]
                if not remaining_tags:
                    n_consumed = len(in0)   # consume all input, nothing left to align to
                    break
                tag = remaining_tags[0]
                pkt_len = pmt.to_long(tag.value)
                self._pad_remaining = self._draw_gap_samples()
                self._in_packet = True
                self._pkt_remaining = pkt_len
                skip = int(tag.offset - current_abs)
                n_consumed += skip

        self._abs_offset += n_consumed
        self.consume(0, n_consumed)   # ← now valid: basic_block allows decoupled consume/produce
        return n_written