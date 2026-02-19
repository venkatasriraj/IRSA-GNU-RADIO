"""
Embedded Python Block: File Source to Tagged Stream
"""

import numpy as np
from gnuradio import gr
import time
import pmt
import os.path
import sys
import base64

"""
State definitions
    0   idle
    1   send preamble
    2   send file data
    3   send file name
    4   send post filler
"""

class blk(gr.sync_block):
    def __init__(self, FileName='None', Pkt_len=52):
        gr.sync_block.__init__(
            self,
            name='EPB: File Source to Tagged Stream',
            in_sig=None,
            out_sig=[np.uint8]
        )

        self.FileName = FileName
        self.Pkt_len = Pkt_len
        self.state = 0      # idle state
        self.pre_count = 0
        self.indx = 0
        self._debug = 0     # debug
        self.data = ""
        self.nitems_written = 0

        if os.path.exists(self.FileName):
            self.f_in = open(self.FileName, 'rb')
            self._eof = False
            if self._debug:
                print("File name:", self.FileName)
            self.state = 1
        else:
            print(self.FileName, 'does not exist')
            self._eof = True
            self.state = 0

        self.char_list = [
            37,85,85,85,85,85,85,85,85,85,85,85,85,85,85,85,
            85,85,85,85,85,85,85,85,85,85,85,85,85,85,85,85,
            85,85,85,85,85,85,85,85,85,85,85,85,85,85,85,85,
            85,85,85,93
        ]
        self.c_len = len(self.char_list)

        self.filler = [
            37,85,85,85,35,69,79,70,
            85,85,85,85,85,85,85,85,
            85,85,85,85,85,85,85,85,
            85,85,85,85,85,85,85,85,
            85,85,85,85,85,85,85,85,
            85,85,85,85,85,85,85,85,
            85,85,85,93
        ]
        self.f_len = len(self.filler)

        header = [
            0xAA,                # preamble
            user_id >> 8,
            user_id & 0xFF,
            pkt_idx >> 8,
            pkt_idx & 0xFF,
            payload_len >> 8,
            payload_len & 0xFF,
            pkt_type             # data / filename / eof
        ]


    def work(self, input_items, output_items):

        if self.state == 0:
            return 0

        elif self.state == 1:
            if self._debug:
                print("state = 1", self.pre_count)

            key1 = pmt.intern("packet_len")
            val1 = pmt.from_long(self.c_len)

            if len(output_items[0]) < self.c_len:
                return 0

            self.add_item_tag(
                0,
                self.nitems_written,
                key1,
                val1
            )

            self.indx += self.c_len
            self.nitems_written += self.c_len

            i = 0
            while i < self.c_len:
                output_items[0][i] = self.char_list[i]
                i += 1

            self.pre_count += 1
            if self.pre_count > 64:
                self.pre_count = 0
                self.state = 2

            return self.c_len

        elif self.state == 2:
            buff = self.f_in.read(self.Pkt_len)
            b_len = len(buff)

            if b_len == 0:
                print('End of file')
                self._eof = True
                self.f_in.close()
                self.state = 3
                self.pre_count = 0
                return 0

            encoded = base64.b64encode(buff)
            e_len = len(encoded)

            if self._debug:
                print('b64 length =', e_len)

            key0 = pmt.intern("packet_len")
            val0 = pmt.from_long(e_len)

            if len(output_items[0]) < e_len:
                return 0

            self.add_item_tag(
                0,
                self.nitems_written,
                key0,
                val0
            )

            self.indx += e_len
            self.nitems_written += e_len

            i = 0
            while i < e_len:
                output_items[0][i] = encoded[i]
                i += 1

            return e_len

        elif self.state == 3:
            fn_len = len(self.FileName)

            key1 = pmt.intern("packet_len")
            val1 = pmt.from_long(fn_len + 8)

            if len(output_items[0]) < fn_len + 8:
                return 0

            self.add_item_tag(
                0,
                self.nitems_written,
                key1,
                val1
            )

            self.indx += fn_len + 8
            self.nitems_written += fn_len + 8

            i = 0
            while i < 8:
                output_items[0][i] = self.filler[i]
                i += 1

            j = 0
            while i < (fn_len + 8):
                output_items[0][i] = ord(self.FileName[j])
                i += 1
                j += 1

            self.state = 4
            return fn_len + 8

        elif self.state == 4:
            if self._debug:
                print("state = 4", self.pre_count)

            key1 = pmt.intern("packet_len")
            val1 = pmt.from_long(self.f_len)

            if len(output_items[0]) < self.f_len:
                return 0

            self.add_item_tag(
                0,
                self.nitems_written,
                key1,
                val1
            )

            self.indx += self.f_len
            self.nitems_written += self.f_len

            i = 0
            while i < self.f_len:
                output_items[0][i] = self.filler[i]
                i += 1

            self.pre_count += 1
            if self.pre_count > 16:
                self.pre_count = 0
                self.state = 0

            return self.f_len

        return 0
