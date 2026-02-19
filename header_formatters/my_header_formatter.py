import struct
from gnuradio import digital

class my_header_formatter(digital.header_format_base):
    def __init__(self):
        # IMPORTANT: use super() and positional args
        super().__init__(
            5,              # header length in BYTES
            "packet_len"    # length tag key
        )

    def format(self, packet_len, tags):
        user_id = 0
        packet_index = 0

        for t in tags:
            if t.key == "user_id":
                user_id = int(t.value)
            elif t.key == "packet_index":
                packet_index = int(t.value)

        # Big-endian: uint8, uint16, uint16
        return struct.pack(">BHH", user_id, packet_index, packet_len)
