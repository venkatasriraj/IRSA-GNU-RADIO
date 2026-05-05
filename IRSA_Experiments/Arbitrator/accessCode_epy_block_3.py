import numpy as np
from gnuradio import gr
import pmt
import csv
import time

class access_code_correlator(gr.sync_block):
    """
    Bitwise sliding-window access code correlator (no CRC).

    Input  : stream of unpacked bits (uint8, values 0 or 1)
             — straight from Differential Decoder output.
    Output : same bit stream, passed through unchanged.
    Message: 'pdu_out' — fires a PDU for every detected packet.

    Packet wire format (no CRC block in TX chain):
        [access_code : 4 B]   <- correlated against, then consumed
        [seq_num     : 2 B big-endian uint16]
        [user_id     : 2 B big-endian uint16]
        [random data : (packet_size - 8) B]

    Parameters
    ----------
    packet_size : int
        Total bytes produced by Random_Packet_Generator (default 100).
    threshold : int
        Minimum bit matches out of 32 to accept access code (default 28).
    log_file : str
        Path for the CSV log of decoded packets.
    """

    ACCESS_CODE_BYTES = [0xE1, 0x5A, 0xE8, 0x93]   # must match TX

    def __init__(self,
                 packet_size=100,
                 threshold=28,
                 log_file="rx_decoded_packets.csv"):

        gr.sync_block.__init__(self,
            name="access_code_correlator",
            in_sig=[np.uint8],
            out_sig=[np.uint8])          # passthrough

        self.message_port_register_out(pmt.intern('pdu_out'))

        self.packet_size = int(packet_size)
        self.threshold   = int(threshold)
        self.log_file    = log_file

        # Access code as bit array, MSB first per byte
        self.ac_bits = np.array(
            [int(b) for byte in self.ACCESS_CODE_BYTES
                     for b in format(byte, '08b')],
            dtype=np.uint8
        )
        self.ac_len = len(self.ac_bits)   # 32

        # After consuming the 4-byte AC, collect the rest of the packet:
        # seq(2) + uid(2) + random(packet_size - 8) = packet_size - 4 bytes
        self.post_ac_bits = (packet_size - 4) * 8

        # Internal state
        self._buf          = np.empty(0, dtype=np.uint8)
        self._state        = 'SEARCH'
        self._collect_bits = []
        self._pkt_count    = 0

        # CSV init
        with open(self.log_file, 'w', newline='') as f:
            csv.writer(f).writerow([
                'pkt_index', 'rx_time', 'user_id', 'seq_num',
                'payload_hex', 'payload_len_bytes'
            ])

    # -- Helpers -------------------------------------------------------

    @staticmethod
    def _bits_to_bytes(bits):
        """Pack flat bit list/array (MSB first) into list of ints."""
        result = []
        for i in range(len(bits) // 8):
            byte = 0
            for b in bits[i*8 : i*8+8]:
                byte = (byte << 1) | int(b)
            result.append(byte)
        return result

    # -- Packet processing ---------------------------------------------

    def _process_packet(self, collect_bits):
        raw_bytes = self._bits_to_bytes(collect_bits)

        # Need at least seq(2) + uid(2) = 4 bytes
        if len(raw_bytes) < 4:
            print(f"[AC_CORR] WARNING: packet too short ({len(raw_bytes)} B), discarding")
            return

        seq_num = (raw_bytes[0] << 8) | raw_bytes[1]
        user_id = (raw_bytes[2] << 8) | raw_bytes[3]
        payload = raw_bytes[4:]

        self._pkt_count += 1

        print(
            f"[AC_CORR PKT {self._pkt_count:04d}] "
            f"user_id={user_id}  "
            f"seq_num={seq_num} ({seq_num:#06x})  "
            f"payload={len(payload)} B"
        )

        now     = time.time()
        rx_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now)) \
                  + f".{int((now % 1) * 1000):03d}"
        pay_hex = ' '.join(f'{b:02X}' for b in payload)

        with open(self.log_file, 'a', newline='') as f:
            csv.writer(f).writerow([
                self._pkt_count, rx_time, user_id, seq_num,
                pay_hex, len(payload)
            ])

        meta = pmt.make_dict()
        meta = pmt.dict_add(meta, pmt.intern('user_id'), pmt.from_long(user_id))
        meta = pmt.dict_add(meta, pmt.intern('seq_num'),  pmt.from_long(seq_num))
        pdu  = pmt.cons(meta, pmt.init_u8vector(len(raw_bytes), raw_bytes))
        self.message_port_pub(pmt.intern('pdu_out'), pdu)

    # -- GNU Radio work() ----------------------------------------------

    def work(self, input_items, output_items):
        in0  = input_items[0]
        out0 = output_items[0]
        out0[:] = in0                    # passthrough

        self._buf = np.concatenate([self._buf, in0])

        while True:

            if self._state == 'SEARCH':
                if len(self._buf) < self.ac_len:
                    break

                # Vectorised correlation - entire buffer in one numpy call
                n_windows = len(self._buf) - self.ac_len + 1
                strides   = (self._buf.strides[0], self._buf.strides[0])
                windows   = np.lib.stride_tricks.as_strided(
                                self._buf,
                                shape=(n_windows, self.ac_len),
                                strides=strides)
                corrs = np.sum(windows == self.ac_bits, axis=1)
                hits  = np.where(corrs >= self.threshold)[0]

                if len(hits) == 0:
                    self._buf = self._buf[-(self.ac_len - 1):]
                    break

                idx = int(hits[0])
                print(f"[AC_CORR] Access code @ buf[{idx}] corr={int(corrs[idx])}/32")
                self._buf          = self._buf[idx + self.ac_len:]
                self._state        = 'COLLECT'
                self._collect_bits = []

            elif self._state == 'COLLECT':
                still_need = self.post_ac_bits - len(self._collect_bits)

                if len(self._buf) >= still_need:
                    self._collect_bits.extend(self._buf[:still_need].tolist())
                    self._buf = self._buf[still_need:]
                    self._process_packet(self._collect_bits)
                    self._state = 'SEARCH'
                    # loop - another packet may follow immediately
                else:
                    self._collect_bits.extend(self._buf.tolist())
                    self._buf = np.empty(0, dtype=np.uint8)
                    break

        return len(in0)