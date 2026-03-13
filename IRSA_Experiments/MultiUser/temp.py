import numpy as np
from gnuradio import gr
import pmt
import time   # ← ADD THIS
import csv    # ← Move this here too (avoid re-importing inside the loop)

class blk(gr.basic_block):
    def __init__(self, output_file="output.bin", log_file="rx_log.csv"):
        gr.basic_block.__init__(self, name="EPB: Decode Packet",
            in_sig=None, out_sig=None)
        self.message_port_register_in(pmt.intern("pdu_in"))
        self.message_port_register_out(pmt.intern("pdu_out"))
        self.set_msg_handler(pmt.intern("pdu_in"), self.handle_pdu)
        self.log_file = log_file
        self.rx_count = 0
        with open(self.log_file, 'w', newline='') as f:
            csv.writer(f).writerow([
                'rx_count', 'timestamp', 'user_id',
                'seq_num', 'crc_ok', 'data_hex'
            ])

    def handle_pdu(self, pdu):
        meta = pmt.car(pdu)
        data = pmt.cdr(pdu)

        # ── Extract user_id and seq_num from metadata ──────────────
        user_id = -1
        seq_num = -1
        if pmt.is_dict(meta):
            if pmt.dict_has_key(meta, pmt.intern("user_id")):
                user_id = pmt.to_long(
                    pmt.dict_ref(meta, pmt.intern("user_id"), pmt.PMT_NIL))
            if pmt.dict_has_key(meta, pmt.intern("seq_num")):
                seq_num = pmt.to_long(
                    pmt.dict_ref(meta, pmt.intern("seq_num"), pmt.PMT_NIL))

        # ── Decode payload ──────────────────────────────────────────
        bytes_out = bytes(pmt.u8vector_elements(data))
        data_hex  = ' '.join(f'{b:02X}' for b in bytes_out)

        self.rx_count += 1
        timestamp = time.strftime('%H:%M:%S')

        print(f"[RX {self.rx_count:03d}] User={user_id} "
              f"Seq={seq_num} | {data_hex[:20]}...")

        # ── Log ────────────────────────────────────────────────────
        with open(self.log_file, 'a', newline='') as f:
            csv.writer(f).writerow([
                self.rx_count, timestamp, user_id,
                seq_num, True, data_hex
            ])

        self.message_port_pub(pmt.intern("pdu_out"), pdu)

'''
How to Measure ALOHA Performance from the Logs

Once both TX logs and this RX log are running, you can directly compute:

Packet Delivery Ratio = RX packets decoded / TX packets sent per user

Collision rate = slots where both users tagged same offset /
                 total slots

Throughput = successfully decoded packets / total slots
'''


class blk(gr.basic_block):
    def __init__(self, output_file="output.bin", log_file="rx_log.csv"):
        gr.basic_block.__init__(self, name="EPB: Decode Packet",
            in_sig=None, out_sig=None)
        self.message_port_register_in(pmt.intern("pdu_in"))
        self.message_port_register_out(pmt.intern("pdu_out"))
        self.set_msg_handler(pmt.intern("pdu_in"), self.handle_pdu)
        self.log_file = log_file
        self.rx_count = 0

        # Initialize log
        with open(self.log_file, 'w', newline='') as f:
            import csv
            csv.writer(f).writerow([
                'rx_count', 'timestamp', 'user_id', 
                'seq_num', 'crc_ok', 'data_hex'
            ])

    def handle_pdu(self, pdu):
        meta = pmt.car(pdu)
        data = pmt.cdr(pdu)

        # ── Extract user_id and seq_num from metadata ──────────────
        user_id = -1
        seq_num = -1
        if pmt.is_dict(meta):
            if pmt.dict_has_key(meta, pmt.intern("user_id")):
                user_id = pmt.to_long(
                    pmt.dict_ref(meta, pmt.intern("user_id"), pmt.PMT_NIL))
            if pmt.dict_has_key(meta, pmt.intern("seq_num")):
                seq_num = pmt.to_long(
                    pmt.dict_ref(meta, pmt.intern("seq_num"), pmt.PMT_NIL))

        # ── Decode payload ──────────────────────────────────────────
        bytes_out = bytes(pmt.u8vector_elements(data))
        data_hex  = ' '.join(f'{b:02X}' for b in bytes_out)

        self.rx_count += 1
        timestamp = time.strftime('%H:%M:%S')

        print(f"[RX {self.rx_count:03d}] User={user_id} "
              f"Seq={seq_num} | {data_hex[:20]}...")

        # ── Log ────────────────────────────────────────────────────
        with open(self.log_file, 'a', newline='') as f:
            import csv
            csv.writer(f).writerow([
                self.rx_count, timestamp, user_id,
                seq_num, True, data_hex
            ])

        self.message_port_pub(pmt.intern("pdu_out"), pdu)

'''
How to Measure ALOHA Performance from the Logs

Once both TX logs and this RX log are running, you can directly compute:

Packet Delivery Ratio = RX packets decoded / TX packets sent per user

Collision rate = slots where both users tagged same offset /
                 total slots

Throughput = successfully decoded packets / total slots
'''
