from gnuradio import gr
import numpy as np

class DebugBits(gr.sync_block):
    def __init__(self, print_len=64):
        gr.sync_block.__init__(
            self,
            name="DebugBits",
            in_sig=[np.uint8],
            out_sig=[np.uint8]
        )
        self.print_len = print_len
        self.counter = 0

    def work(self, input_items, output_items):
        data = input_items[0]
        out = output_items[0]

        out[:] = data

        # Print only first few samples (avoid flooding)
        if self.counter < 5:
            bits = ''.join(str(int(b)) for b in data[:self.print_len])
            print(f"[DEBUG] Bits: {bits}")
            self.counter += 1

        return len(out)