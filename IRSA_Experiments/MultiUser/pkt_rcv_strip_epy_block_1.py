#!/usr/bin/env python
from gnuradio import gr
import pmt
import time

class blk(gr.sync_block):
    def __init__(self, filename="pdu_log.txt"):
        gr.sync_block.__init__(
            self,
            name="pdu_logger",
            in_sig=None,
            out_sig=None
        )
        self.message_port_register_in(pmt.intern('pdu_in'))
        self.message_port_register_out(pmt.intern('pdu_out'))
        self.set_msg_handler(pmt.intern('pdu_in'), self.handle_pdu)
        
        self.log_file = open(filename, 'w')
        self.packet_count = 0
        
    def handle_pdu(self, pdu):
        # Log PDU metadata
        meta = pmt.car(pdu)
        data = pmt.cdr(pdu)
        
        timestamp = time.time()
        self.packet_count += 1
        
        # Write to log file
        log_entry = f"Packet {self.packet_count} | Time: {timestamp} | "
        log_entry += f"Length: {pmt.length(data)} bytes\n"
        
        if pmt.is_dict(meta):
            log_entry += f"Metadata: {pmt.to_python(meta)}\n"
        
        self.log_file.write(log_entry)
        self.log_file.flush()
        
        # Pass PDU through
        self.message_port_pub(pmt.intern('pdu_out'), pdu)
    
    def __del__(self):
        self.log_file.close()