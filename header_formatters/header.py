import struct
import crcmod

class irsa_header_formatter:
    HEADER_LEN = 12

    def __init__(self, access_key=0xABCD):
        self.access_key = access_key
        self.crc16 = crcmod.predefined.mkCrcFun('crc-ccitt-false')

    def format(self, payload_len, tags):
        """
        payload_len : int
        tags        : dict (can carry user_id, slot_id, etc.)
        """

        user_id   = tags.get("user_id", 0)
        #packet_id = tags.get("packet_id", 0)
        #slot_id   = tags.get("slot_id", 0)

        header_wo_crc = struct.pack(
            "!HHHHH",
            self.access_key,
            user_id,
            #packet_id,
            #slot_id,
            payload_len
        )

        crc = self.crc16(header_wo_crc)
        header = header_wo_crc + struct.pack("!H", crc)

        return header
