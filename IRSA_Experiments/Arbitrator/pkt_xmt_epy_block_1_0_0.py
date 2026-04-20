#!/usr/bin/env python
from gnuradio import gr
import numpy as np
import time
import csv

class iq_logger_with_timestamp(gr.sync_block):
    def __init__(self, iq_csv_filename="iq_samples.csv"):
        gr.sync_block.__init__(
            self,
            name="iq_logger_with_timestamp",
            in_sig=[np.complex64],
            out_sig=[np.complex64]
        )

        self.iq_csv_filename = iq_csv_filename
        self.sample_count = 0

        # Initialize CSV with header (same pattern as Random_Packet_Generator)
        with open(self.iq_csv_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'sample_index',
                'timestamp',
                'num_samples',
                'i_values',
                'q_values'
            ])

    def work(self, input_items, output_items):
        in0 = input_items[0]
        out0 = output_items[0]

        # Timestamp with millisecond precision (matches Random_Packet_Generator style)
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S') + \
                    f".{int((time.time() % 1) * 1000):03d}"

        num_samples = len(in0)

        # Split complex64 into separate I and Q lists
        i_values = in0.real.tolist()
        q_values = in0.imag.tolist()

        # Append row to CSV
        with open(self.iq_csv_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                self.sample_count,
                timestamp,
                num_samples,
                i_values,
                q_values
            ])

        self.sample_count += num_samples

        # Pass samples through unchanged
        out0[:] = in0
        return len(out0)

    def stop(self):
        print(f"[IQ Logger] Finished. Total samples logged: {self.sample_count}")
        return True
