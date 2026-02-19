from gnuradio import gr
import pmt
import random
import time
import threading

class Random_Packet_Generator(gr.basic_block):
    def __init__(self, mean_interval=0.1, packet_size=100):
        gr.basic_block.__init__(self,
            name="random_packet_generator",
            in_sig=None,
            out_sig=None)
        self.message_port_register_out(pmt.intern('pdu_out'))
        self.mean_interval = mean_interval
        self.packet_size = packet_size
        self.total_packets = 100
        self.packet_count = 0
        self.thread = threading.Thread(target=self.generate_packets)
        self.thread.daemon = True
        self.thread.start()
    
    def generate_packets(self):
        while self.packet_count < self.total_packets:
            # Random wait time (uniform distribution)
            #wait_time = random.uniform(0, 2 * self.mean_interval)
            wait_time = random.expovariate(1.0 / self.mean_interval)
            time.sleep(wait_time)
            
            # Generate random packet data
            data = [random.randint(0, 255) for _ in range(self.packet_size)]
            pdu = pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(data), data))
            self.packet_count += 1
            self.message_port_pub(pmt.intern('pdu_out'), pdu)
            print(f"Packet transmitted after {wait_time:.3f}s wait")