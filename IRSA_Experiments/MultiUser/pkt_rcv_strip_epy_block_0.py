import numpy as np
from gnuradio import gr
import pmt
import time
import csv


class blk(gr.basic_block):
    """
    EPB: Decode Packet

    Extracts seq_num and user_id from the fixed 4-byte payload header
    that was embedded by random_packet_generator at TX:

        byte 0-1 : seq_num  (big-endian uint16)
        byte 2-3 : user_id  (big-endian uint16)
        byte 4+  : random payload

    Logs every received packet to CSV and forwards the full PDU
    downstream (to PDU to Tagged Stream → File Sink).
    """

    def __init__(self, output_file="output.bin", log_file="rx_log.csv"):
        gr.basic_block.__init__(self,
            name="EPB: Decode Packet",
            in_sig=None,
            out_sig=None)

        self.message_port_register_in(pmt.intern("pdu_in"))
        self.message_port_register_out(pmt.intern("pdu_out"))
        self.set_msg_handler(pmt.intern("pdu_in"), self.handle_pdu)

        self.log_file  = log_file
        self.rx_count  = 0

        # Initialise log file with header
        with open(self.log_file, 'w', newline='') as f:
            csv.writer(f).writerow([
                'rx_count', 'timestamp',
                'user_id', 'seq_num',
                'payload_len', 'data_hex'
            ])

    # ------------------------------------------------------------------
    def handle_pdu(self, pdu):
        # PDU = (meta, data)  — data is the full byte vector from CRC32
        data_bytes = bytes(pmt.u8vector_elements(pmt.cdr(pdu)))

        # ── Validate minimum length ────────────────────────────────
        if len(data_bytes) < 4:
            print(f"[RX] WARNING: packet too short ({len(data_bytes)} bytes), skipping")
            return

        # ── Extract header fields from payload bytes ───────────────
        #    DO NOT read from PMT metadata — it is gone after demod
        seq_num = (data_bytes[0] << 8) | data_bytes[1]   # bytes 0-1
        user_id = (data_bytes[2] << 8) | data_bytes[3]   # bytes 2-3
        payload = data_bytes[4:]                          # bytes 4+

        # ── Logging ────────────────────────────────────────────────
        self.rx_count += 1
        timestamp = (time.strftime('%Y-%m-%d %H:%M:%S') +
                     f".{int((time.time() % 1) * 1000):03d}")
        data_hex  = ' '.join(f'{b:02X}' for b in data_bytes)

        print(f"[RX {self.rx_count:03d}] user_id={user_id} "
              f"seq={seq_num:#06x} "
              f"payload_len={len(payload)} "
              f"| first 4B: {data_hex.split()[:4]}")

        with open(self.log_file, 'a', newline='') as f:
            csv.writer(f).writerow([
                self.rx_count,
                timestamp,
                user_id,
                seq_num,
                len(payload),
                data_hex
            ])

        # ── Forward full PDU downstream ────────────────────────────
        # Stream CRC32 (Check mode) already discarded bad packets,
        # so every packet reaching here is CRC-valid.
        self.message_port_pub(pmt.intern("pdu_out"), pdu)