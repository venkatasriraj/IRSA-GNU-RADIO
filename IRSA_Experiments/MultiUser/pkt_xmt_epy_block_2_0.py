from gnuradio import gr
import pmt
import random
import time
import threading
import csv
import os

class Random_Packet_Generator(gr.basic_block):
    def __init__(self, mean_interval=0.1, packet_size=100, log_file="transmitted_packets.csv"):
        gr.basic_block.__init__(self,
            name="random_packet_generator",
            in_sig=None,
            out_sig=None)
        self.message_port_register_out(pmt.intern('pdu_out'))
        self.mean_interval = mean_interval
        self.packet_size = packet_size
        self.total_packets = 100
        self.packet_count = 0
        self.log_file = log_file

        # Initialize log file with header
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['packet_id', 'timestamp', 'wait_time_s', 'data_hex', 'data_bytes'])

        self.thread = threading.Thread(target=self.generate_packets)
        self.thread.daemon = True
        self.thread.start()

    def generate_packets(self):
        while self.packet_count < self.total_packets:
            wait_time = random.expovariate(1.0 / self.mean_interval)
            time.sleep(wait_time)

            # Generate random packet data
            data = [random.randint(0, 255) for _ in range(self.packet_size)]

            # Publish to GNU Radio message port
            pdu = pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(data), data))
            self.packet_count += 1
            self.message_port_pub(pmt.intern('pdu_out'), pdu)

            # ── Log the packet ──────────────────────────────────────────
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S') + f".{int((time.time() % 1) * 1000):03d}"
            data_hex   = ' '.join(f'{b:02X}' for b in data)   # e.g. "A3 FF 01 ..."
            data_bytes = list(data)                             # plain int list

            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    self.packet_count,
                    timestamp,
                    f"{wait_time:.4f}",
                    data_hex,
                    data_bytes
                ])
            # ───────────────────────────────────────────────────────────

            print(f"[PKT {self.packet_count:03d}] Transmitted after {wait_time:.3f}s | "
                  f"First 4 bytes: {data_hex.split()[:4]}")
