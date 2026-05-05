import numpy as np
from gnuradio import gr
import pmt
import queue

class blk(gr.basic_block):
    """
    PDU Passthrough — accepts PDU burst from Tagged Stream to PDU,
    outputs the raw IQ samples as a stream. No zero-padding, no ALOHA logic.
    Use this to verify PDU → stream conversion is working correctly.
    """

    def __init__(self):
        gr.basic_block.__init__(
            self,
            name="PDU Passthrough",
            in_sig=[],
            out_sig=[np.complex64]
        )
        self.message_port_register_in(pmt.intern("burst_in"))
        self.set_msg_handler(pmt.intern("burst_in"), self._handle_pdu)

        self._queue        = queue.Queue()
        self._burst        = None
        self._burst_offset = 0

    def _handle_pdu(self, msg):
        try:
            payload = pmt.cdr(msg)
            samples = np.array(pmt.c32vector_elements(payload), dtype=np.complex64)
            self._queue.put(samples)
            print(f"[PDU Passthrough] received burst: {len(samples)} samples")
        except Exception as e:
            print(f"[PDU Passthrough] error: {e}")

    def general_work(self, input_items, output_items):
        out      = output_items[0]
        n_out    = len(out)
        produced = 0

        while produced < n_out:
            if self._burst is None:
                try:
                    self._burst        = self._queue.get_nowait()
                    self._burst_offset = 0
                except queue.Empty:
                    out[produced:n_out] = np.complex64(0)
                    produced = n_out
                    break

            burst_remaining = len(self._burst) - self._burst_offset
            space_left      = n_out - produced
            n_copy          = min(burst_remaining, space_left)

            out[produced : produced + n_copy] = \
                self._burst[self._burst_offset : self._burst_offset + n_copy]

            self._burst_offset += n_copy
            produced           += n_copy

            if self._burst_offset >= len(self._burst):
                self._burst        = None
                self._burst_offset = 0

        return produced