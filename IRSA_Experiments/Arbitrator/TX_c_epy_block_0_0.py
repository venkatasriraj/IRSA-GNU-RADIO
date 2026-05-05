import numpy as np
from gnuradio import gr
import pmt
import time
import csv

class blk(gr.basic_block):
    """
    EPB: Decode Packet
    Updated to handle packets with Preambles and CRCs.
    """

    def __init__(self, log_file="rx_log.csv", preamble_present=False):
        gr.basic_block.__init__(self,
            name="EPB: Decode Packet",
            in_sig=None,
            out_sig=None)

        self.message_port_register_in(pmt.intern("pdu_in"))
        self.message_port_register_out(pmt.intern("pdu_out"))
        self.set_msg_handler(pmt.intern("pdu_in"), self.handle_pdu)

        self.log_file = log_file
        self.rx_count = 0
        # If your Correlator DOES NOT strip the preamble, set this to 4
        self.header_start_offset = 4 if preamble_present else 0

        # Initialize log file
        with open(self.log_file, 'w', newline='') as f:
            csv.writer(f).writerow([
                'rx_count', 'timestamp', 'total_pdu_len',
                'user_id', 'seq_num', 'payload_len', 'data_hex'
            ])

    def handle_pdu(self, pdu):
        # Extract data bytes from PDU
        data_bytes = bytes(pmt.u8vector_elements(pmt.cdr(pdu)))
        total_len = len(data_bytes)

        # 1. Minimum Length Check 
        # (Header=4B, so min len is offset + 4)
        min_required = self.header_start_offset + 4
        if total_len < min_required:
            print(f"[RX] WARNING: Packet too short ({total_len} bytes). Expected at least {min_required}B.")
            return

        # 2. Extract Header Fields 
        # Offsets shift based on whether the Access Code is still in the buffer
        idx = self.header_start_offset
        
        seq_num = (data_bytes[idx] << 8) | data_bytes[idx+1]
        user_id = (data_bytes[idx+2] << 8) | data_bytes[idx+3]
        payload = data_bytes[idx+4:]

        # 3. Diagnostic Logging
        self.rx_count += 1
        timestamp = (time.strftime('%Y-%m-%d %H:%M:%S') +
                     f".{int((time.time() % 1) * 1000):03d}")
        data_hex = ' '.join(f'{b:02X}' for b in data_bytes)

        # Print detailed info to console for debugging collisions
        print(f"[RX {self.rx_count:03d}] LEN={total_len}B | UID={user_id} | SEQ={seq_num:#06x} | Payload={len(payload)}B")

        with open(self.log_file, 'a', newline='') as f:
            csv.writer(f).writerow([
                self.rx_count, timestamp, total_len,
                user_id, seq_num, len(payload), data_hex
            ])

        # 4. Forward PDU downstream
        self.message_port_pub(pmt.intern("pdu_out"), pdu)