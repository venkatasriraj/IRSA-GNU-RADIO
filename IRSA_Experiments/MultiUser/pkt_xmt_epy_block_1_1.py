#!/usr/bin/env python
from gnuradio import gr
import numpy as np
import time
import struct

class iq_logger_with_timestamp(gr.sync_block):
    def __init__(self, iq_filename="iq_samples.dat", 
                 timestamp_filename="timestamps.txt"):
        gr.sync_block.__init__(
            self,
            name="iq_logger_with_timestamp",
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )
        
        self.iq_file = open(iq_filename, 'wb')
        self.timestamp_file = open(timestamp_filename, 'w')
        self.sample_count = 0
        
    def work(self, input_items, output_items):
        in0 = input_items[0]
        out0 = output_items[0]
        
        # Get current timestamp
        timestamp = time.time()
        
        # Write I-Q samples to binary file
        self.iq_file.write(in0.tobytes())
        
        # Log timestamp with sample count
        num_samples = len(in0)
        log_entry = f"{timestamp},{self.sample_count},{num_samples}\n"
        self.timestamp_file.write(log_entry)
        self.timestamp_file.flush()
        
        self.sample_count += num_samples
        
        # Pass samples through
        out0[:] = in0
        
        return len(out0)
    
    def stop(self):
        self.iq_file.close()
        self.timestamp_file.close()
        return True


# ```

# Save this as `iq_logger_with_timestamp.py`

# ### In GRC:
# ```
# [Modulator] → [Custom IQ Logger] → [USRP Sink]

