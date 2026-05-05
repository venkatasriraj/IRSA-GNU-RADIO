import numpy as np
from gnuradio import gr
import pmt
import collections

class PDU_to_Timed_Byte_Stream(gr.sync_block):
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name='PDU to Timed Byte Stream',
            in_sig=None,
            out_sig=[np.uint8, np.uint8] # Port 0: Data, Port 1: Gate
        )
        self.message_port_register_in(pmt.intern("pdus"))
        self.set_msg_handler(pmt.intern("pdus"), self.handle_msg)
        
        self.byte_buffer = collections.deque()
        # Track the start of new packets for tagging
        self.packet_lengths = collections.deque() 
        self.bytes_left_in_packet = 0

    def handle_msg(self, msg):
        data = pmt.u8vector_elements(pmt.cdr(msg))
        p_len = len(data)
        # Store the data and the length of this specific packet
        for b in data:
            self.byte_buffer.append(b)
        self.packet_lengths.append(p_len)

    def work(self, input_items, output_items):
        out_data = output_items[0]
        out_gate = output_items[1]
        n = len(out_data)

        for i in range(n):
            if self.byte_buffer:
                # Logic to detect the exact start of a burst
                if self.bytes_left_in_packet == 0 and self.packet_lengths:
                    self.bytes_left_in_packet = self.packet_lengths.popleft()
                    
                    # Add the Stream Tag
                    key = pmt.intern("burst_start")
                    value = pmt.from_long(1)
                    # self.add_item_tag(0, self.nitems_written(0) + i, key, value)
                    self.add_item_tag(1, self.nitems_written(1) + i, key, value)
                
                out_data[i] = self.byte_buffer.popleft()
                out_gate[i] = 1
                # if i==0 or i==n-1:
                #     print("gate activated at index", i)
                #     print(n, self.bytes_left_in_packet)
                
                if self.bytes_left_in_packet > 0:
                    self.bytes_left_in_packet -= 1
            else:
                out_data[i] = 0
                out_gate[i] = 0
                self.bytes_left_in_packet = 0 # Reset just in case

        return n