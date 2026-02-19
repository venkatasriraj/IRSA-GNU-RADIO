#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Strip preamble and trailer packets from input file,
then decode Base64 payload into original binary data.
"""

import os
import sys
import base64
import re

# ---------------- CONFIG ----------------
DEBUG = False

PKT_LEN = 252          # preamble packet size
FILENAME_MAX = 44

STATE_PREAMBLE = 0
STATE_DATA = 1
STATE_DONE = 2
# ----------------------------------------


def debug(msg):
    if DEBUG:
        print(msg)


if len(sys.argv) < 3:
    print("Usage: python3 strip_preamble.py <input file> <output file>")
    sys.exit(1)

in_fn = sys.argv[1]
out_fn = sys.argv[2]

if not os.path.exists(in_fn):
    print(in_fn, "does not exist")
    sys.exit(1)

state = STATE_PREAMBLE
b64_buf = b""   # Base64 accumulation buffer

with open(in_fn, "rb") as f_in, open(out_fn, "wb") as f_out:

    while True:

        # ---------- PREAMBLE STRIP ----------
        if state == STATE_PREAMBLE:
            buff = f_in.read(PKT_LEN)
            if len(buff) < PKT_LEN:
                break

            # detect preamble packet
            if buff[0] == 37 and buff[51] == 93:   # '%' and ']'
                debug("Preamble packet skipped")
                continue

            debug("End of preamble detected")
            state = STATE_DATA
            # fall through intentionally (do NOT continue)

        # ---------- DATA STATE ----------
        if state == STATE_DATA:
            buff = f_in.read(4)
            if len(buff) == 0:
                debug("EOF reached")
                break

            # trailer detection
            if buff.startswith(b"%"):
                if buff == b"%UUU":
                    print("End of text")

                    # skip next four 'U's
                    f_in.read(4)

                    # read transmitted filename
                    name_bytes = []
                    for _ in range(FILENAME_MAX):
                        ch = f_in.read(1)
                        if not ch or ch == b"%":
                            break
                        name_bytes.append(ch.decode("ascii", errors="ignore"))

                    ofn = "".join(name_bytes)
                    print("Transmitted file name:", ofn)

                    state = STATE_DONE
                    break

            # -------- Base64 handling --------
            # Remove non-base64 chars (GNU Radio safety)
            buff = re.sub(rb'[^A-Za-z0-9+/=]', b'', buff)

            b64_buf += buff

            # Decode only full base64 blocks
            valid_len = (len(b64_buf) // 4) * 4
            if valid_len:
                try:
                    data = base64.b64decode(b64_buf[:valid_len])
                    f_out.write(data)
                    b64_buf = b64_buf[valid_len:]
                except Exception as e:
                    print("Base64 decode error:", e)
                    break

# -------- flush remaining base64 --------
if b64_buf:
    try:
        data = base64.b64decode(b64_buf)
        with open(out_fn, "ab") as f_out:
            f_out.write(data)
    except Exception:
        pass

print("Done.")
