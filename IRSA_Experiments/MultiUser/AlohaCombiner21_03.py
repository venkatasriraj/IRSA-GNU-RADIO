#!/usr/bin/env python3
"""
aloha_combiner.py
-----------------
Receives IQ chunks from TX1 and TX2 via separate ZMQ PULL sockets.
Aligns both streams onto a shared wall-clock timeline, detects whether
the current output window has samples from one TX only or from both
(collision), sums them, and forwards the result to the channel server
via ZMQ PUSH.

Wire format (TX → combiner):
    [8 bytes: int64 local_sample_index] + [N * 8 bytes: complex64 samples]
    N is nominally CHUNK_SIZE but the last chunk of a packet may be shorter.

Wire format (combiner → channel):
    Same layout: [8 bytes: int64 global_sample_index] + [N * 8 bytes: complex64]

Ports (defaults, override via CLI args or constants below):
    TX1  →  tcp://localhost:5555   (combiner BINDs)
    TX2  →  tcp://localhost:5556   (combiner BINDs)
    OUT  →  tcp://localhost:5557   (combiner CONNECTs to channel server)
"""

import zmq
import numpy as np
import struct
import time
import argparse
from collections import defaultdict
from datetime import datetime

# ── Parameters ────────────────────────────────────────────────────────────────
SAMPLE_RATE  = 768_000          # samples / second
CHUNK_SIZE   = 4_096            # nominal samples per chunk
TICK_INTERVAL = CHUNK_SIZE / SAMPLE_RATE   # ~5.33 ms

TX1_BIND  = "tcp://*:5555"
TX2_BIND  = "tcp://*:5556"
CH_CONNECT = "tcp://localhost:5557"

# How many chunks to buffer ahead per TX before warnings
MAX_BUFFER_CHUNKS = 512

# Silence threshold: amplitude below this → treat as padding zeros
SILENCE_THRESHOLD = 1e-6

HEADER_FMT  = "q"   # int64
HEADER_SIZE = struct.calcsize(HEADER_FMT)   # 8 bytes

# ── Helpers ───────────────────────────────────────────────────────────────────

def pack_chunk(global_idx: int, samples: np.ndarray) -> bytes:
    return struct.pack(HEADER_FMT, global_idx) + samples.astype(np.complex64).tobytes()

def unpack_chunk(data: bytes):
    """Returns (local_sample_index, complex64_array). Array may be shorter than CHUNK_SIZE."""
    local_idx = struct.unpack(HEADER_FMT, data[:HEADER_SIZE])[0]
    samples = np.frombuffer(data[HEADER_SIZE:], dtype=np.complex64).copy()
    return local_idx, samples

def is_active(samples: np.ndarray) -> bool:
    """True if the chunk carries real signal (not all-zeros padding)."""
    return float(np.max(np.abs(samples))) > SILENCE_THRESHOLD

def rms(samples: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.abs(samples)**2)))

# ── Main combiner ─────────────────────────────────────────────────────────────

class ALOHACombiner:
    def __init__(self, tx1_bind=TX1_BIND, tx2_bind=TX2_BIND, ch_connect=CH_CONNECT):
        self.ctx = zmq.Context()
        self.ctx.setsockopt(zmq.LINGER, 0)

        # Two PULL sockets — one per TX
        self.pull_tx1 = self.ctx.socket(zmq.PULL)
        self.pull_tx1.setsockopt(zmq.LINGER, 0)
        self.pull_tx1.setsockopt(zmq.RCVHWM, MAX_BUFFER_CHUNKS)
        self.pull_tx1.bind(tx1_bind)

        self.pull_tx2 = self.ctx.socket(zmq.PULL)
        self.pull_tx2.setsockopt(zmq.LINGER, 0)
        self.pull_tx2.setsockopt(zmq.RCVHWM, MAX_BUFFER_CHUNKS)
        self.pull_tx2.bind(tx2_bind)

        # PUSH to channel server
        self.push_ch = self.ctx.socket(zmq.PUSH)
        self.push_ch.setsockopt(zmq.LINGER, 0)
        self.push_ch.setsockopt(zmq.SNDHWM, MAX_BUFFER_CHUNKS)
        self.push_ch.connect(ch_connect)

        # Poller for non-blocking receive from both TXs
        self.poller = zmq.Poller()
        self.poller.register(self.pull_tx1, zmq.POLLIN)
        self.poller.register(self.pull_tx2, zmq.POLLIN)

        # Timeline buffers: global_sample_index → complex64 array
        # global_sample_index = round((recv_time - T0) * SAMPLE_RATE) aligned to CHUNK_SIZE
        self.buf: dict[str, dict[int, np.ndarray]] = {
            "tx1": {},
            "tx2": {},
        }

        self.epoch: float | None = None   # T0 wall-clock time (seconds)
        self.output_cursor: int = 0       # next global sample index to send
        self.chunk_count: int = 0         # total output chunks sent

        # Stats
        self.stats = defaultdict(int)     # SILENCE / TX1_ONLY / TX2_ONLY / COLLISION

        print(f"[combiner] Listening TX1 on {tx1_bind}")
        print(f"[combiner] Listening TX2 on {tx2_bind}")
        print(f"[combiner] Forwarding to channel {ch_connect}")
        print(f"[combiner] SAMPLE_RATE={SAMPLE_RATE}, CHUNK_SIZE={CHUNK_SIZE}, "
              f"TICK={TICK_INTERVAL*1000:.3f} ms")

    # ── Timeline helpers ───────────────────────────────────────────────────────

    def _global_idx(self, recv_time: float) -> int:
        """Convert a wall-clock receive time to the nearest aligned global sample index."""
        if self.epoch is None:
            self.epoch = recv_time
            return 0
        elapsed_samples = (recv_time - self.epoch) * SAMPLE_RATE
        # Align to CHUNK_SIZE grid
        chunk_no = round(elapsed_samples / CHUNK_SIZE)
        return int(chunk_no * CHUNK_SIZE)

    def _drain_sockets(self):
        """Non-blocking: pull all available chunks from both TX sockets into buffers."""
        while True:
            ready = dict(self.poller.poll(timeout=0))   # 0 ms → non-blocking
            if not ready:
                break
            recv_time = time.time()

            for sock, key in [(self.pull_tx1, "tx1"), (self.pull_tx2, "tx2")]:
                if sock not in ready:
                    continue
                try:
                    data = sock.recv(zmq.NOBLOCK)
                except zmq.Again:
                    continue

                _local_idx, samples = unpack_chunk(data)
                g_idx = self._global_idx(recv_time)

                # If a chunk already exists at this slot (can happen with tiny timing jitter),
                # append samples contiguously rather than overwriting.
                if g_idx in self.buf[key]:
                    existing = self.buf[key][g_idx]
                    combined = np.zeros(max(len(existing), len(samples)), dtype=np.complex64)
                    combined[:len(existing)] += existing
                    combined[:len(samples)]  += samples
                    self.buf[key][g_idx] = combined
                else:
                    self.buf[key][g_idx] = samples

                if len(self.buf[key]) > MAX_BUFFER_CHUNKS:
                    oldest = min(self.buf[key])
                    del self.buf[key][oldest]
                    print(f"[combiner] WARNING: {key} buffer overflow, dropped chunk @ {oldest}")

    # ── Output step ───────────────────────────────────────────────────────────

    def _step(self):
        """
        Produce one output chunk at output_cursor.

        Classification:
            SILENCE    – neither TX has signal here
            TX1_ONLY   – only TX1 has signal
            TX2_ONLY   – only TX2 has signal
            COLLISION  – both TXs have signal (samples are summed)
        """
        s1 = self.buf["tx1"].pop(self.output_cursor, None)
        s2 = self.buf["tx2"].pop(self.output_cursor, None)

        active1 = (s1 is not None) and is_active(s1)
        active2 = (s2 is not None) and is_active(s2)

        # Build output array (CHUNK_SIZE long, or shorter if end-of-packet)
        length = CHUNK_SIZE
        if s1 is not None:
            length = max(length, len(s1))
        if s2 is not None:
            length = max(length, len(s2))

        out = np.zeros(length, dtype=np.complex64)

        if active1:
            out[:len(s1)] += s1
        if active2:
            out[:len(s2)] += s2

        # Classify
        if active1 and active2:
            label = "COLLISION"
        elif active1:
            label = "TX1_ONLY"
        elif active2:
            label = "TX2_ONLY"
        else:
            label = "SILENCE"

        self.stats[label] += 1

        # Log non-silence events
        if label != "SILENCE":
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            rms1 = rms(s1) if active1 else 0.0
            rms2 = rms(s2) if active2 else 0.0
            print(f"[{ts}] chunk={self.chunk_count:6d}  g_idx={self.output_cursor:9d}"
                  f"  {label:<10s}  RMS tx1={rms1:.4f}  tx2={rms2:.4f}")

        # Send to channel
        payload = pack_chunk(self.output_cursor, out)
        self.push_ch.send(payload)

        self.output_cursor += length
        self.chunk_count += 1

    # ── Run loop ──────────────────────────────────────────────────────────────

    def run(self):
        print("[combiner] Running. Press Ctrl-C to stop.\n")
        deadline = time.perf_counter() + TICK_INTERVAL

        try:
            while True:
                now = time.perf_counter()

                if now >= deadline:
                    self._drain_sockets()
                    self._step()
                    # Advance deadline by one tick; if we fell behind, catch up gently
                    deadline += TICK_INTERVAL
                    if time.perf_counter() - deadline > TICK_INTERVAL * 4:
                        deadline = time.perf_counter() + TICK_INTERVAL
                else:
                    # Sleep only a fraction of the remaining time to stay responsive
                    remaining = deadline - now
                    time.sleep(remaining * 0.8)

        except KeyboardInterrupt:
            self._print_summary()
        finally:
            self._cleanup()

    def _print_summary(self):
        total = sum(self.stats.values())
        print("\n── Summary ─────────────────────────────────────────────")
        for label in ("TX1_ONLY", "TX2_ONLY", "COLLISION", "SILENCE"):
            n = self.stats[label]
            pct = 100 * n / total if total else 0
            bar = "█" * int(pct / 2)
            print(f"  {label:<12s}  {n:6d} chunks  ({pct:5.1f}%)  {bar}")
        print(f"  Total output chunks : {total}")
        print(f"  Output samples      : {self.output_cursor}")
        print(f"  Output duration     : {self.output_cursor / SAMPLE_RATE * 1000:.1f} ms")
        print("─────────────────────────────────────────────────────────\n")

    def _cleanup(self):
        print("[combiner] Closing sockets …")
        self.pull_tx1.close()
        self.pull_tx2.close()
        self.push_ch.close()
        self.ctx.term()
        print("[combiner] Done.")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="ALOHA channel combiner")
    p.add_argument("--tx1-bind",   default=TX1_BIND,   help="ZMQ bind for TX1 PULL socket")
    p.add_argument("--tx2-bind",   default=TX2_BIND,   help="ZMQ bind for TX2 PULL socket")
    p.add_argument("--ch-connect", default=CH_CONNECT, help="ZMQ connect for channel PUSH socket")
    args = p.parse_args()

    combiner = ALOHACombiner(
        tx1_bind=args.tx1_bind,
        tx2_bind=args.tx2_bind,
        ch_connect=args.ch_connect,
    )
    combiner.run()


if __name__ == "__main__":
    main()