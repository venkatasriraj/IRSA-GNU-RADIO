#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust replacement for strip_e.py:
- context-managed file IO
- reliable preamble search (n_preamble consecutive packets)
- stream-safe Base64 decoding with trailer (%UUU) detection across chunk boundaries
- tolerant final-block decoding
- minimal debug via _debug flag
"""

import os
import sys
import base64
import binascii

_debug = 0
Pkt_len = 52
B64_LEN = 72
n_preamble = 64
TRAILER_MARK = b'%UUU'

def read_next_byte_from_buf_then_file(buf, buf_pos, f_in):
    # yields (byte, new_buf_pos, buf_consumed_flag)
    if buf_pos < len(buf):
        return buf[buf_pos:buf_pos+1], buf_pos + 1, True
    b = f_in.read(1)
    return b, buf_pos, False

def decode_and_write(b64_bytes, f_out):
    if not b64_bytes:
        return
    # decode as many full 4-byte blocks as possible
    full_len = (len(b64_bytes) // 4) * 4
    to_decode = b64_bytes[:full_len]
    rem = b64_bytes[full_len:]
    if to_decode:
        try:
            data = base64.b64decode(to_decode, validate=True)
        except binascii.Error:
            # fallback: tolerant decode
            data = base64.b64decode(to_decode, validate=False)
        f_out.write(data)
    return rem  # return leftover (<4 bytes) to prepend next time

def main():
    if len(sys.argv) < 3:
        print('Usage: python3 strip_e_fixed.py <input file> <output file>')
        return 1

    fn = sys.argv[1]
    if not os.path.exists(fn):
        print(fn, 'does not exist')
        return 1

    with open(fn, 'rb') as f_in, open(sys.argv[2], 'wb') as f_out:
        # Preamble search: need n_preamble consecutive packets
        consec = 0
        while True:
            pkt = f_in.read(Pkt_len)
            if not pkt:
                if _debug:
                    print('EOF while searching preamble')
                return 0
            if len(pkt) < Pkt_len:
                if _debug:
                    print('Short packet while searching preamble:', len(pkt))
                return 0
            if pkt[0] == ord('%') and pkt[51] == ord(']'):
                consec += 1
                if _debug:
                    print('preamble match', consec)
                if consec >= n_preamble:
                    break
                continue
            # mismatch: reset counter and continue scanning
            if _debug:
                print('preamble mismatch, resetting counter')
            consec = 0

        # Enter Base64 decode state. Use a rolling buffer to detect trailer across boundaries.
        stream_buf = bytearray()
        leftover = bytearray()  # leftover <4 bytes from previous decode
        while True:
            chunk = f_in.read(B64_LEN)
            if not chunk:
                # EOF: attempt to decode any remaining buffered base64
                if leftover:
                    # pad leftover to multiple of 4 and decode tolerant
                    pad_len = (-len(leftover)) % 4
                    try:
                        data = base64.b64decode(leftover + b'=' * pad_len, validate=False)
                        f_out.write(data)
                    except Exception:
                        if _debug:
                            print('Final decode failed')
                return 0

            stream_buf.extend(chunk)

            # search for trailer marker anywhere in buffer
            idx = stream_buf.find(TRAILER_MARK)
            if idx != -1:
                # decode everything before marker
                before = bytes(stream_buf[:idx])
                if leftover:
                    before = bytes(leftover) + before
                    leftover = bytearray()
                # decode full blocks
                rem = decode_and_write(before, f_out)
                # rem is leftover (<4 bytes) - ignore for trailer boundary
                # consume data up to idx + len(TRAILER_MARK)
                post_pos = idx + len(TRAILER_MARK)

                # The original logic skips four additional 'U's after the marker.
                # Try to skip up to 4 additional bytes 'U' if present; read from buffer/file as needed.
                skip_needed = 4
                # Build a small buffer to consume skip+filename bytes
                tail_buf = stream_buf[post_pos:]
                # If tail_buf is short, read more from file into tail_buf
                if len(tail_buf) < skip_needed:
                    extra = f_in.read(skip_needed - len(tail_buf))
                    tail_buf += extra or b''
                # Remove leading Us (up to 4)
                u_skip = 0
                while u_skip < skip_needed and u_skip < len(tail_buf) and tail_buf[u_skip: u_skip+1] == b'U':
                    u_skip += 1
                tail_buf = tail_buf[u_skip:]

                # Now read filename bytes from tail_buf then from file until '%' or EOF
                fname_bytes = bytearray()
                # consume from tail_buf first
                pos = 0
                while pos < len(tail_buf):
                    b = tail_buf[pos:pos+1]
                    pos += 1
                    if b == b'%' or b == b'':
                        break
                    fname_bytes.extend(b)
                # if we didn't find terminator, continue reading from file
                if pos >= len(tail_buf) or (pos < len(tail_buf) and tail_buf[pos-1:pos] != b'%'):
                    while True:
                        ch = f_in.read(1)
                        if not ch or ch == b'%':
                            break
                        fname_bytes.extend(ch)

                try:
                    ofn = fname_bytes.decode('utf-8', errors='replace')
                except Exception:
                    ofn = repr(fname_bytes)
                print('End of text. Transmitted file name:', ofn)
                return 0

            # No trailer found: decode as much base64 as possible from the buffer
            # Prepend leftover (<4) from previous iteration
            to_process = bytes(leftover) + bytes(stream_buf)
            # Keep at most as many full 4-byte blocks as possible; keep a small tail (<4*2) to handle marker across boundary
            full_blocks_len = (len(to_process) // 4) * 4
            # but avoid decoding the very last up-to-8 bytes to allow marker straddling; we'll keep last 8 bytes
            safe_decode_len = max(0, full_blocks_len - 8)
            if safe_decode_len > 0:
                to_decode = to_process[:safe_decode_len]
                try:
                    decoded = base64.b64decode(to_decode, validate=True)
                except binascii.Error:
                    decoded = base64.b64decode(to_decode, validate=False)
                f_out.write(decoded)
                # new leftover is bytes after safe_decode_len
                leftover = bytearray(to_process[safe_decode_len:])
                stream_buf = bytearray()  # consumed everything from stream_buf into to_process
            else:
                # Not enough to safely decode; keep accumulating
                # limit buffer size to avoid uncontrolled growth
                if len(stream_buf) > 10 * B64_LEN:
                    # force-decode the largest safe part
                    full_blocks_len = (len(to_process) // 4) * 4
                    if full_blocks_len > 0:
                        to_decode = to_process[:full_blocks_len]
                        try:
                            decoded = base64.b64decode(to_decode, validate=True)
                        except binascii.Error:
                            decoded = base64.b64decode(to_decode, validate=False)
                        f_out.write(decoded)
                        leftover = bytearray(to_process[full_blocks_len:])
                        stream_buf = bytearray()
                    else:
                        # give up and clear buffer
                        if _debug:
                            print('Clearing oversized buffer')
                        stream_buf = bytearray()
                        leftover = bytearray()

if __name__ == '__main__':
    sys.exit(main() or 0)