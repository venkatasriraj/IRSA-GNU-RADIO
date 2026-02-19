
"""
Docstring for pkt_rcv_decode_old

old code of decode part before saving into the file the code is 
updated on: 18-02-2026
"""
import numpy as np
from gnuradio import gr
import pmt

class blk(gr.sync_block):
    def __init__(self, output_file="decoded_packets.bin"):
        gr.sync_block.__init__(
            self,
            name='EPB: Decode Packet',
            in_sig=None,
            out_sig=None)
        self.message_port_register_in(pmt.intern('msg_in'))
        self.message_port_register_out(pmt.intern('msg_out'))
        self.set_msg_handler(pmt.intern('msg_in'), self.handle_msg)
        
        self.output_file = output_file
        self.packet_count = 0
        
    def handle_msg(self, msg):
        _debug = 1  # set to 1 for diagnostics, 0 to disable
        
        try:
            # Extract the data portion from PDU
            buff = pmt.to_python(pmt.cdr(msg))
        except Exception as e:
            gr.log.error("Error with message conversion: %s" % str(e))
            return
        
        if buff is None or len(buff) == 0:
            gr.log.warn("Received empty packet")
            return
            
        b_len = len(buff)
        self.packet_count += 1
        
        if _debug:
            print(f"\n=== Packet #{self.packet_count} ===")
            print(f"Length: {b_len} bytes")
            print(f"Data (hex): {' '.join(f'{b:02x}' for b in buff[:min(32, b_len)])}")
            if b_len > 32:
                print(f"... ({b_len - 32} more bytes)")
        
        # Convert to numpy array for easier manipulation
        data = np.frombuffer(buff, dtype=np.uint8)
        
        # Store to file
        try:
            with open(self.output_file, 'wb') as f:  # append binary mode
                # Write packet with header: [packet_len (2 bytes)][data]
                header = np.array([b_len & 0xFF, (b_len >> 8) & 0xFF], dtype=np.uint8)
                header.tofile(f)
                data.tofile(f)
            
            if _debug:
                print(f"Saved to: {self.output_file}")
                
        except Exception as e:
            gr.log.error(f"Error writing to file: {str(e)}")
        
        # Forward the packet downstream
        pdu = pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(data), list(data)))
        self.message_port_pub(pmt.intern('msg_out'), pdu)