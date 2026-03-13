#!/usr/bin/env python
from gnuradio import gr
import pmt
import time
import csv


class blk(gr.basic_block):   # ← MUST be basic_block, not sync_block
    """
    PDU Logger

    Logs every PDU that passes through to a text log and a CSV.
    Also extracts seq_num and user_id from the fixed 4-byte payload
    header so you can check whether packets are arriving at all,
    even if EPB Decode Packet is not printing anything.

    Payload header (set by random_packet_generator):
        bytes 0-1 : seq_num  (big-endian uint16)
        bytes 2-3 : user_id  (big-endian uint16)
        bytes 4+  : random payload
    """

    def __init__(self, filename="log.txt"):
        gr.basic_block.__init__(       # ← basic_block init
            self,
            name="pdu_logger",
            in_sig=None,
            out_sig=None
        )
        self.message_port_register_in(pmt.intern('pdu_in'))
        self.message_port_register_out(pmt.intern('pdu_out'))
        self.set_msg_handler(pmt.intern('pdu_in'), self.handle_pdu)

        self.packet_count   = 0
        self.bad_crc_count  = 0   # incremented if crc_fail tag seen
        self.filename       = filename

        # ── Text log ──────────────────────────────────────────────
        self.log_file = open(filename, 'w')
        self.log_file.write("=== PDU Logger started ===\n")
        self.log_file.flush()

        # ── CSV log (same folder, .csv extension) ─────────────────
        csv_name = filename.replace('.txt', '_pdu.csv') \
                   if filename.endswith('.txt') else filename + '.csv'
        self._csv_fh = open(csv_name, 'w', newline='')
        self._csv    = csv.writer(self._csv_fh)
        self._csv.writerow([
            'pkt_num', 'timestamp',
            'user_id', 'seq_num',
            'pkt_len_bytes', 'crc_ok',
            'first_8_bytes_hex'
        ])
        self._csv_fh.flush()

    # ------------------------------------------------------------------
    def handle_pdu(self, pdu):
        meta       = pmt.car(pdu)
        data_vec   = pmt.cdr(pdu)
        data_bytes = bytes(pmt.u8vector_elements(data_vec))
        pkt_len    = len(data_bytes)

        self.packet_count += 1
        timestamp = (time.strftime('%Y-%m-%d %H:%M:%S') +
                     f".{int((time.time() % 1)*1000):03d}")

        # ── Extract seq_num / user_id from payload bytes ──────────
        #    (PMT metadata keys are gone after demodulation)
        seq_num = user_id = -1
        if pkt_len >= 4:
            seq_num = (data_bytes[0] << 8) | data_bytes[1]
            user_id = (data_bytes[2] << 8) | data_bytes[3]

        # ── Check if CRC-fail tag is present in metadata ──────────
        crc_ok = True
        if pmt.is_dict(meta):
            if pmt.dict_has_key(meta, pmt.intern('crc_fail')):
                crc_ok = False
                self.bad_crc_count += 1

        first8 = ' '.join(f'{b:02X}' for b in data_bytes[:8])

        # ── Text log ──────────────────────────────────────────────
        line = (f"[PKT {self.packet_count:04d}] {timestamp} "
                f"user_id={user_id} seq={seq_num:#06x} "
                f"len={pkt_len} crc={'OK' if crc_ok else 'FAIL'} "
                f"| {first8}\n")
        self.log_file.write(line)
        self.log_file.flush()

        # ── CSV log ───────────────────────────────────────────────
        self._csv.writerow([
            self.packet_count, timestamp,
            user_id, seq_num,
            pkt_len, crc_ok,
            first8
        ])
        self._csv_fh.flush()

        # ── Console (visible in GRC terminal) ────────────────────
        print(f"[PDU_LOG {self.packet_count:04d}] "
              f"user={user_id} seq={seq_num} "
              f"len={pkt_len} crc={'OK' if crc_ok else 'FAIL'}")

        # ── Pass PDU through unchanged ────────────────────────────
        self.message_port_pub(pmt.intern('pdu_out'), pdu)

    # ------------------------------------------------------------------
    def __del__(self):
        try:
            summary = (f"\n=== Session ended | "
                       f"Total: {self.packet_count} | "
                       f"CRC fail: {self.bad_crc_count} ===\n")
            self.log_file.write(summary)
            self.log_file.close()
            self._csv_fh.close()
        except Exception:
            pass