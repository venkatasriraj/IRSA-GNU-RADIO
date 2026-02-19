#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Title: strip_preamble
# Author: Barry Duggan

"""
Strip preamble and trailer packets from input file.
Then convert Base64 to original input.
"""

import os.path
import sys
import base64

_debug = 0          # set to zero to turn off diagnostics
state = 0
Pkt_len = 52
B64_LEN = 72     # Base64 length for 52 bytes

if len(sys.argv) < 3:
    print('Usage: python3 strip_preamble.py <input file> <output file>')
    print('Number of arguments=', len(sys.argv))
    print('Argument List:', str(sys.argv))
    exit(1)

# test if input file exists
fn = sys.argv[1]
if not os.path.exists(fn):
    print(fn, 'does not exist')
    exit(1)

# open input file
f_in = open(fn, 'rb')

# open output file
f_out = open(sys.argv[2], 'wb')

i = 0
n_preamble = 57

while True:

    if state == 0:
        eof = False
        while i < n_preamble:

            buff = f_in.read(Pkt_len)
            if len(buff) == 0:
                # EOF reached — stop outer loop
                #print('EOF reached while scanning preamble')
                eof = True
                break
            if len(buff) < Pkt_len:
                # partial read near EOF — treat as EOF
                print('Short read near EOF:', len(buff))
                eof = True
                break

            # still in preamble
            if buff[0] == ord('%') and buff[51] == ord(']'):
                i += 1
            else:
                break
        if eof:
            # hit EOF while scanning preamble — stop
            break
        if i == n_preamble:
            state = 1
            continue
            

    elif state == 1:
        buff = f_in.read(B64_LEN)
        b_len = len(buff)

        if b_len == 0:
            print('End of file')
            break

        if b_len < B64_LEN:
            print('Short base64 read near EOF:', b_len)
            try:
                data = base64.b64decode(buff)
                f_out.write(data)
            except Exception as e:
                print("Base64 decode error on final block:", e)
            break

        if buff[:4] == b'%UUU':      # trailer marker
            print("End of text")

            buff = f_in.read(4)     # skip next four 'U's
            rcv_fn = []

            while True:
                ch = f_in.read(1)
                if ch == b'%' or len(ch) == 0:
                    break
                rcv_fn.append(chr(ch[0]))

            ofn = "".join(rcv_fn)
            print("Transmitted file name:", ofn)

            state = 2
            break

        else:
            # decode Base64
            try:
                data = base64.b64decode(buff, validate=True)
                f_out.write(data)
            except Exception as e:
                print("Base64 decode error:", e)

f_in.close()
f_out.close()
