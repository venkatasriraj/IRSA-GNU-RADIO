"""
epy_slot_combiner.py
====================
Embedded Python Block — Pure ALOHA Channel Combiner (Source Block)

Purpose
-------
Simulates the physical superposition of RF signals from multiple users
in a Pure ALOHA channel. Pulls IQ samples from N ZMQ PUSH/PULL sockets
and adds their chunks sample-by-sample into a single combined output —
exactly like signals superposing in the air at an antenna.

How collision works
-------------------
No slot tracking or timeout needed. Collision is implicit:
  • Both users transmitting same chunk period → chunks added → collision
  • Only one user transmitting              → that chunk passed through
  • Nobody transmitting                     → zeros output (silence)

This models Pure ALOHA (continuous time), NOT Slotted ALOHA.

Chunk alignment
---------------
ZMQ recv() does not guarantee fixed message sizes, so a per-user
raw byte accumulator is maintained. Every poll cycle, exactly
CHUNK_SIZE samples are extracted from each accumulator (if available)
and added into the combined output. The accumulator is NOT a slot
buffer — it only ever holds partial ZMQ messages, never more than
one chunk at a time under normal operation.

Port assignments (match pkt_xmt_tc_pull.grc ZMQ PUSH Sinks):
  User 1 → tcp://127.0.0.1:49212   (PUSH connects here)
  User 2 → tcp://127.0.0.1:49213   (PUSH connects here)

Add more users by extending ADDRESSES and adding addr params.

Parameters
----------
CHUNK_SIZE   : samples processed per poll cycle.
               1024 is a safe default — matches GNU Radio's typical
               work() buffer granularity. Smaller = lower latency,
               larger = better throughput.
ZMQ_POLL_MS  : how long to wait for any socket activity per cycle.
               Keep small (1-5ms) so silence periods output zeros
               promptly without stalling the stream.
"""

import numpy as np
from gnuradio import gr
import zmq
import threading
import queue
import atexit

# Global registry to track bound addresses
_BOUND_ADDRESSES = set()

# ─────────────────────────────────────────────
#  Configuration — edit to match your GRC
# ─────────────────────────────────────────────
ADDRESSES   = [
    "tcp://127.0.0.1:49212",   # User 1
    "tcp://127.0.0.1:49213",   # User 2
]
CHUNK_SIZE  = 1024   # samples per processing cycle (complex64)
ZMQ_POLL_MS = 2      # poller wait time per cycle (ms)


class blk(gr.sync_block):
    """Pure ALOHA Combiner — source block, 0 inputs, 1 complex output."""

    def __init__(self,
                 addr1=ADDRESSES[0],
                 addr2=ADDRESSES[1],
                 chunk_size=CHUNK_SIZE,
                 zmq_poll_ms=ZMQ_POLL_MS):

        gr.sync_block.__init__(
            self,
            name="Pure ALOHA Combiner",
            in_sig=None,               # SOURCE — no stream inputs
            out_sig=[np.complex64]
        )

        self.chunk_size   = chunk_size
        self.zmq_poll_ms  = zmq_poll_ms
        self.addresses    = [addr1, addr2]
        self.num_users    = len(self.addresses)
        self._chunk_bytes = chunk_size * 8   # complex64 = 8 bytes/sample

        # ── ZMQ setup ──────────────────────────────────────────────────
        self.ctx     = zmq.Context()
        self.sockets = []
        self.poller  = zmq.Poller()
        self._bound_addrs = []  # Track what THIS instance bound
        

        for (i,addr) in enumerate(self.addresses):
            sock = self.ctx.socket(zmq.PULL)
            sock.setsockopt(zmq.LINGER, 0)  # 100ms recv timeout to prevent blocking
            # Check if already bound by another instance
            if addr in _BOUND_ADDRESSES:
                print(f"[PureALOHA] WARNING: {addr} already bound "
                      f"(likely a duplicate GRC instance). Skipping this block.")
                # Don't bind - this is a duplicate instantiation
                sock.close()
                continue

            try:
                sock.bind(addr)
                _BOUND_ADDRESSES.add(addr)
                self._bound_addrs.append(addr)
                self.poller.register(sock, zmq.POLLIN)
                self.sockets.append(sock)
                print(f"[PureALOHA] User {i+1} bound to {addr} ✓")
            except zmq.error.ZMQError as e:
                print(f"[PureALOHA] ERROR: Cannot bind to {addr}: {e}")
                sock.close()
                self._cleanup()
                raise

            # Only start thread if we actually bound sockets
        if len(self.sockets) == 0:
            print("[PureALOHA] No sockets bound - this is a duplicate instance, doing nothing.")
            self._running = False
            return

         # ── Per-user byte accumulators ──────────────────────────────
        self._raw_buf = [b"" for _ in range(len(self.sockets))]

        # ── Output queue → work() ───────────────────────────────────
        self._out_q   = queue.Queue()
        self._out_buf = np.array([], dtype=np.complex64)

        # ── Background thread ───────────────────────────────────────
        self._running = True
        self._thread  = threading.Thread(target=self._receiver_loop,
                                         daemon=True)
        self._thread.start()

    def _cleanup(self):
        """Clean up bound addresses from global registry."""
        for addr in self._bound_addrs:
            _BOUND_ADDRESSES.discard(addr)
        for sock in self.sockets:
            try:
                sock.close()
            except:
                pass
        try:
            self.ctx.term()
        except:
            pass

    # ──────────────────────────────────────────────────────────────────
    #  Background thread
    # ──────────────────────────────────────────────────────────────────
    def _receiver_loop(self):
        while self._running:

            # ── Step 1: drain all ready sockets into per-user accumulators
            ready = dict(self.poller.poll(self.zmq_poll_ms))

            for uid, sock in enumerate(self.sockets):
                if sock in ready:
                    try:
                        self._raw_buf[uid] += sock.recv()
                    except zmq.Again:
                        pass

            # ── Step 2: extract exactly chunk_size samples per user ─────
            combined      = np.zeros(self.chunk_size, dtype=np.complex64)
            active_users  = []

            for uid in range(self.num_users):
                if len(self._raw_buf[uid]) >= self._chunk_bytes:
                    chunk_bytes          = self._raw_buf[uid][:self._chunk_bytes]
                    self._raw_buf[uid]   = self._raw_buf[uid][self._chunk_bytes:]
                    combined            += np.frombuffer(chunk_bytes,
                                                         dtype=np.complex64)
                    active_users.append(uid + 1)

            # ── Step 3: log and push to output queue ────────────────────
            if len(active_users) > 1:
                print(f"[PureALOHA] COLLISION — Users {active_users} "
                      f"combined into {self.chunk_size} samples")
            elif len(active_users) == 1:
                print(f"[PureALOHA] User {active_users[0]} — "
                      f"{self.chunk_size} samples passed through")

            # Always output a chunk (zeros = silence) — keeps stream alive
            self._out_q.put(combined)

    # ──────────────────────────────────────────────────────────────────
    #  GNU Radio work() — drains output queue into the stream
    # ──────────────────────────────────────────────────────────────────
    def work(self, input_items, output_items):
        out      = output_items[0]
        n_wanted = len(out)

        # Refill internal buffer from queue
        while len(self._out_buf) < n_wanted:
            try:
                chunk = self._out_q.get_nowait()
                self._out_buf = np.concatenate([self._out_buf, chunk])
            except queue.Empty:
                break

        if len(self._out_buf) == 0:
            out[:] = 0
            return n_wanted

        n_out           = min(n_wanted, len(self._out_buf))
        out[:n_out]     = self._out_buf[:n_out]
        self._out_buf   = self._out_buf[n_out:]

        if n_out < n_wanted:
            out[n_out:] = 0

        return n_wanted

    # ──────────────────────────────────────────────────────────────────
    #  Cleanup
    # ──────────────────────────────────────────────────────────────────
    def stop(self):
        self._running = False
        self._thread.join(timeout=1.0)
        for sock in self.sockets:
            sock.close()
        self.ctx.term()
        return True
