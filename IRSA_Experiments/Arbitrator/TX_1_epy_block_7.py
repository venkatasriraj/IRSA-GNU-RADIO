import numpy as np
from gnuradio import gr
import pmt
import queue
import time

class blk(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(
            self,
            name="PDU Passthrough (Verified)",
            in_sig=[],
            out_sig=[np.complex64],
        )
        self.message_port_register_in(pmt.intern("burst_in"))
        self.set_msg_handler(pmt.intern("burst_in"), self._handle_pdu)

        self._queue = queue.Queue()
        self._burst = None
        self._offset = 0
        self._packet_count = 0  # To verify arrival count

    def _handle_pdu(self, msg):
        try:
            # Extract samples from PDU
            samples = np.array(
                pmt.c32vector_elements(pmt.cdr(msg)),
                dtype=np.complex64,
            )
            self._packet_count += 1
            self._queue.put(samples)
            
            # Detailed Verification Log
            print(f"[VERIFY] Packet #{self._packet_count} received at {time.strftime('%H:%M:%S')}")
            print(f"        Size: {len(samples)} samples")
        except Exception as e:
            print(f"[ERROR] PDU handling failed: {e}")

    def _try_load(self):
        if self._burst is not None:
            return
        try:
            self._burst = self._queue.get_nowait()
            self._offset = 0
        except queue.Empty:
            pass 

    def general_work(self, input_items, output_items):
        out = output_items[0]
        n_out = len(out)
        self._try_load()

        if self._burst is None:
            # Idle state: Send zeros. 
            # Note: This is necessary for RF interference (Summing)
            out[:] = np.complex64(0)
            return n_out

        remaining = len(self._burst) - self._offset
        take = min(n_out, remaining)

        out[:take] = self._burst[self._offset : self._offset + take]

        if take < n_out:
            # Fill the rest of the buffer with zeros if burst ends
            out[take:] = np.complex64(0)

        self._offset += take
        if self._offset >= len(self._burst):
            print(f"[VERIFY] Packet #{self._packet_count} output complete.")
            self._burst = None
            self._offset = 0

        return n_out