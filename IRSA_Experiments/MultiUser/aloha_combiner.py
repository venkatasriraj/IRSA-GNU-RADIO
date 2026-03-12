"""
aloha_combiner.py
=================
Standalone Pure ALOHA Channel Combiner

Sits between the GNU Radio TX flowgraphs and the Channel flowgraph:

    [pkt_xmt User1] --PUSH--> 49212 ──┐
                                       ├─► [aloha_combiner.py] ──PUB──► 49203
    [pkt_xmt User2] --PUSH--> 49213 ──┘
                                       [chan_loopback] SUB connects to 49203
                                       [chan_loopback] PUB binds    at 49201
                                       [pkt_rcv]       SUB connects to 49201

ZMQ socket roles
----------------
  PULL bind  49212  ← User 1 TX does PUSH + connect
  PULL bind  49213  ← User 2 TX does PUSH + connect
  PUB  bind  49203  → chan_loopback ZMQ SUB Source connects here

Usage
-----
  python aloha_combiner.py                     # normal mode
  python aloha_combiner.py --verbose           # print every active cycle
  python aloha_combiner.py --heartbeat 3       # status line every 3 s (default 5)
  python aloha_combiner.py --chunk 1024 --poll 1

Stop with Ctrl-C.
"""

import argparse
import time
import numpy as np
import zmq


# ─────────────────────────────────────────────────────────────────────────────
#  Defaults
# ─────────────────────────────────────────────────────────────────────────────
PULL_ADDRS       = [
    "tcp://127.0.0.1:49212",   # User 1
    "tcp://127.0.0.1:49213",   # User 2
]
PUB_ADDR         = "tcp://127.0.0.1:49203"
CHUNK_SIZE       = 1024   # complex64 samples per processing cycle
ZMQ_POLL_MS      = 2      # poller wait time per cycle (ms)
HEARTBEAT_SECS   = 5      # print status line every N seconds
BYTES_PER_SAMPLE = 8      # complex64


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────
def ts():
    """Short timestamp string for log lines."""
    return time.strftime("%H:%M:%S")


# ─────────────────────────────────────────────────────────────────────────────
#  Core combiner loop
# ─────────────────────────────────────────────────────────────────────────────
def run(chunk_size: int, zmq_poll_ms: int, verbose: bool, heartbeat: float):
    chunk_bytes = chunk_size * BYTES_PER_SAMPLE
    num_users   = len(PULL_ADDRS)

    ctx    = zmq.Context()
    poller = zmq.Poller()

    # ── PULL sockets — one per user ──────────────────────────────────────────
    pull_sockets = []
    for addr in PULL_ADDRS:
        sock = ctx.socket(zmq.PULL)
        sock.setsockopt(zmq.LINGER, 0)      # release port immediately on close
        sock.bind(addr)
        poller.register(sock, zmq.POLLIN)
        pull_sockets.append(sock)
        print(f"[{ts()}] PULL bound  {addr}")

    # ── PUB socket — feeds channel flowgraph ─────────────────────────────────
    pub_sock = ctx.socket(zmq.PUB)
    pub_sock.setsockopt(zmq.LINGER, 0)
    pub_sock.bind(PUB_ADDR)
    # print(f"[{ts()}] PUB  bound  {PUB_ADDR}")
    # print(f"[{ts()}] chunk={chunk_size} samples  poll={zmq_poll_ms} ms  "
    #       f"heartbeat={heartbeat}s")
    # print(f"[{ts()}] Waiting for data ... (Ctrl-C to stop)\n")

    time.sleep(0.1)   # let subscribers connect before first publish

    # ── Per-user byte accumulators ────────────────────────────────────────────
    raw_buf        = [b"" for _ in range(num_users)]

    # ── Counters for heartbeat ────────────────────────────────────────────────
    bytes_recvd    = [0] * num_users
    chunks_flushed = [0] * num_users
    collisions     = 0
    hb_time        = time.time()

    # ── Global summary ────────────────────────────────────────────────────────
    total_chunks     = 0
    total_collisions = 0
    total_single     = 0

    try:
        while True:

            # ── Step 1: drain all ready sockets ──────────────────────────────
            ready = dict(poller.poll(zmq_poll_ms))

            for uid, sock in enumerate(pull_sockets):
                if sock in ready:
                    try:
                        msg = sock.recv(zmq.NOBLOCK)
                        raw_buf[uid]     += msg
                        bytes_recvd[uid] += len(msg)

                        # Always print when raw bytes arrive — confirms TX→combiner link
                        print(f"[{ts()}] <- RAW recv User {uid+1}: "
                              f"{len(msg)} bytes  "
                              f"(accumulator now {len(raw_buf[uid])} bytes)")

                    except zmq.Again:
                        pass

            # ── Step 2: extract one chunk per user ────────────────────────────
            combined     = np.zeros(chunk_size, dtype=np.complex64)
            active_users = []

            for uid in range(num_users):
                if len(raw_buf[uid]) >= chunk_bytes:
                    chunk_b            = raw_buf[uid][:chunk_bytes]
                    raw_buf[uid]       = raw_buf[uid][chunk_bytes:]
                    combined          += np.frombuffer(chunk_b, dtype=np.complex64)
                    active_users.append(uid + 1)
                    chunks_flushed[uid] += 1
                    total_chunks        += 1

            # ── Step 3: log active events ─────────────────────────────────────
            n = len(active_users)
            if n > 1:
                collisions       += 1
                total_collisions += 1
                print(f"[{ts()}] *** COLLISION  users={active_users}  "
                      f"chunk={chunk_size} samples")
            elif n == 1:
                total_single += 1
                if verbose:
                    print(f"[{ts()}] >>> User {active_users[0]}  "
                          f"{chunk_size} samples -> channel")

            # ── Step 4: publish to channel ────────────────────────────────────
            pub_sock.send(combined.tobytes())

            # ── Step 5: periodic heartbeat ────────────────────────────────────
            now = time.time()
            if now - hb_time >= heartbeat:
                buf_sizes = [len(b) for b in raw_buf]
                print(f"\n[{ts()}] -------- HEARTBEAT --------")
                for uid in range(num_users):
                    status = "OK" if bytes_recvd[uid] > 0 else "NO DATA"
                    print(f"  User {uid+1}: [{status}]  "
                          f"recvd={bytes_recvd[uid]} bytes  "
                          f"chunks_out={chunks_flushed[uid]}  "
                          f"pending={buf_sizes[uid]} bytes")
                print(f"  Collisions this interval : {collisions}")
                print(f"  Total chunks published   : {total_chunks}")

                if all(b == 0 for b in bytes_recvd):
                    print(f"  WARNING: NO DATA from any user!")
                    print(f"  Check: Is TX flowgraph running?")
                    print(f"  Check: Does ZMQ PUSH Sink use 'Connect' to 49212/49213?")
                print(f"  ---------------------------\n")

                # reset interval counters
                bytes_recvd    = [0] * num_users
                chunks_flushed = [0] * num_users
                collisions     = 0
                hb_time        = now

    except KeyboardInterrupt:
        print(f"\n[{ts()}] Stopping...")

    finally:
        total = max(total_chunks, 1)
        print(f"\n[{ts()}] -------- FINAL SUMMARY --------")
        print(f"  Total chunks published : {total_chunks}")
        print(f"  Collisions             : {total_collisions} "
              f"({100*total_collisions/total:.1f}%)")
        print(f"  Single-user            : {total_single} "
              f"({100*total_single/total:.1f}%)")
        for sock in pull_sockets:
            sock.close()
        pub_sock.close()
        ctx.term()
        print(f"[{ts()}] Done.")


# ─────────────────────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(
        description="Pure ALOHA combiner — bridges TX ZMQ PUSH to channel ZMQ SUB"
    )
    p.add_argument("--chunk", type=int, default=CHUNK_SIZE,
                   help=f"Samples per processing cycle (default: {CHUNK_SIZE})")
    p.add_argument("--poll",  type=int, default=ZMQ_POLL_MS,
                   help=f"ZMQ poller timeout ms (default: {ZMQ_POLL_MS})")
    p.add_argument("--heartbeat", type=float, default=HEARTBEAT_SECS,
                   help=f"Status print interval in seconds (default: {HEARTBEAT_SECS})")
    p.add_argument("--verbose", action="store_true",
                   help="Print every single-user chunk (can be noisy)")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(chunk_size=args.chunk,
        zmq_poll_ms=args.poll,
        verbose=args.verbose,
        heartbeat=args.heartbeat)