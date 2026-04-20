from gnuradio import gr
import pmt
import random
import time
import threading
import csv

class Random_Packet_Generator(gr.basic_block):
    """
    Random Packet Generator with embedded userid and sequence number.

    Packet payload layout:
        [0:2]  – seq_num  : 2 bytes, big-endian uint16
        [2:4]  – user_id  : 2 bytes, big-endian uint16  (0–65535)
        [4:]   – random data : fills the rest up to packet_size bytes

    The PMT metadata dict carries:
        'packet_num' → seq_num  (used by Packet Header Generator block)
        'user_id'    → user_id  (informational)
    """

    def __init__(self,
                 mean_interval=0.1,
                 packet_size=100,
                 user_id=1,
                 log_file="transmitted_packets.csv"):

        gr.basic_block.__init__(self,
            name="random_packet_generator",
            in_sig=None,
            out_sig=None)

        self.message_port_register_out(pmt.intern('pdu_out'))

        # ── Parameters ────────────────────────────────────────────────
        self.mean_interval = mean_interval
        self.packet_size   = packet_size
        self.user_id       = int(user_id) & 0xFFFF   # clamp to uint16
        self.log_file      = log_file
        self.total_packets = 4
        self.packet_count  = 0

        # Header overhead: seq(2) + user_id(2) = 4 bytes
        if packet_size <= 4:
            raise ValueError(
                f"packet_size ({packet_size}) must be > 4 to fit the header"
            )

        # ── Init CSV log ──────────────────────────────────────────────
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'packet_id', 'timestamp', 'user_id',
                'wait_time_s', 'data_hex', 'data_bytes'
            ])

        # ── Start generator thread ────────────────────────────────────
        self.thread = threading.Thread(target=self._generate_packets, daemon=True)
        self.thread.start()

    # ─────────────────────────────────────────────────────────────────
    def _build_payload(self, seq: int) -> list:
        """
        Assemble the byte payload:
            [seq_hi, seq_lo, uid_hi, uid_lo, *random_bytes]
        """
        header = [
            (seq          >> 8) & 0xFF,   # seq high byte
             seq                & 0xFF,   # seq low byte
            (self.user_id >> 8) & 0xFF,   # user_id high byte
             self.user_id       & 0xFF,   # user_id low byte
        ]
        random_bytes = [random.randint(0, 255)
                        for _ in range(self.packet_size - len(header))]
        return header + random_bytes

    # ─────────────────────────────────────────────────────────────────
    def _generate_packets(self):
        seq = 0
        time.sleep(random.uniform(0, self.mean_interval))
        while self.packet_count < self.total_packets:
            wait_time = random.expovariate(1.0 / self.mean_interval)
            time.sleep(wait_time)

            data = self._build_payload(seq)

            # ── Build PMT metadata dict ───────────────────────────────
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta,
                                pmt.intern('packet_num'),
                                pmt.from_long(seq))             # Packet Header Generator
            meta = pmt.dict_add(meta,
                                pmt.intern('user_id'),
                                pmt.from_long(self.user_id))    # informational

            # ── Publish PDU ───────────────────────────────────────────
            pdu = pmt.cons(meta, pmt.init_u8vector(len(data), data))
            self.message_port_pub(pmt.intern('pdu_out'), pdu)

            self.packet_count += 1
            seq = (seq + 1) & 0xFFFF    # 16-bit rollover

            # ── CSV logging ───────────────────────────────────────────
            timestamp = (time.strftime('%Y-%m-%d %H:%M:%S') +
                         f".{int((time.time() % 1) * 1000):03d}")
            data_hex  = ' '.join(f'{b:02X}' for b in data)

            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    self.packet_count,
                    timestamp,
                    self.user_id,
                    f"{wait_time:.4f}",
                    data_hex,
                    list(data)
                ])

            print(f"[PKT {self.packet_count:03d}] user_id={self.user_id} "
                  f"seq={seq - 1 & 0xFFFF:#06x} "
                  f"after {wait_time:.3f}s | "
                  f"first 4B: {data_hex.split()[:4]}")