"""
epy_slot_combiner.py
====================
Embedded Python Block — ALOHA Slot Combiner (Source Block)

Purpose
-------
Simulates the physical superposition of RF signals from multiple users
in an ALOHA channel. Pulls IQ samples from N ZMQ PUSH/PULL sockets,
detects which users are transmitting in the same slot, and either:
  • ADDs their samples (collision — both transmit same slot)
  • PASSES a single user's samples (no collision)
  • OUTPUTS ZEROS (silence — nobody transmitting)

Why a source block (0 stream inputs)?
---------------------------------------
GNU Radio sync_blocks require all input streams to produce samples
at the same rate. ZMQ PULL blocks only produce output when a message
arrives — if User2 is silent, its PULL block stalls, which stalls
the Add block, which stalls everything. By handling ZMQ directly
inside this block we escape that synchronisation problem entirely.

Port assignments (match pkt_xmt_tc_pull.grc ZMQ PUSH Sinks):
  User 1 → tcp://127.0.0.1:49212   (PUSH connects here)
  User 2 → tcp://127.0.0.1:49213   (PUSH connects here)

Add more users by extending ADDRESSES list and rebuilding.

Slot timing
-----------
packet_samples = 34 079   ← from seq_tagger block in pkt_xmt
  = Packet_Samples value shown in GRC

slot_timeout_ms controls how long we wait for a second user before
deciding the slot belongs to only one user (no collision).
Set it to roughly one packet duration:
  34 079 samples / 768 000 sps ≈ 44 ms  → use 50 ms default
"""

import numpy as np
from gnuradio import gr
import zmq
import threading
import queue
import time


# ─────────────────────────────────────────────
#  Configuration — edit these to match your GRC
# ─────────────────────────────────────────────
ADDRESSES = [
    "tcp://127.0.0.1:49212",   # User 1
    "tcp://127.0.0.1:49213",   # User 2
]
PACKET_SAMPLES  = 34079   # must match seq_tagger → Packet_Samples
SLOT_TIMEOUT_MS = 50      # wait time before declaring no-collision
ZMQ_RECV_MS     = 5       # poll timeout per socket (keep small)


class blk(gr.sync_block):
    """ALOHA Slot Combiner — source block, 0 inputs, 1 complex output."""

    def __init__(self,
                 addr1=ADDRESSES[0],
                 addr2=ADDRESSES[1],
                 packet_samples=PACKET_SAMPLES,
                 slot_timeout_ms=SLOT_TIMEOUT_MS):

        gr.sync_block.__init__(
            self,
            name="ALOHA Slot Combiner",
            in_sig=None,                   # SOURCE — no stream inputs
            out_sig=[np.complex64]
        )

        self.packet_samples   = packet_samples
        self.slot_timeout_ms  = slot_timeout_ms
        self.addresses        = [addr1, addr2]
        self.num_users        = len(self.addresses)

        # ── ZMQ setup ──────────────────────────────────────────────────
        self.ctx     = zmq.Context()
        self.ctx.setsockopt(zmq.LINGER, 0) 
        self.sockets = []
        self.poller  = zmq.Poller()

        for addr in self.addresses:
            sock = self.ctx.socket(zmq.PULL)
            sock.setsockopt(zmq.LINGER, 0)
            sock.set(zmq.RCVTIMEO, ZMQ_RECV_MS)
            sock.bind(addr)               # TX side does PUSH + connect
            self.poller.register(sock, zmq.POLLIN)
            self.sockets.append(sock)
            print(f"[SlotCombiner] Bound ZMQ PULL to {addr}")

        # ── Per-user raw-byte buffers (accumulate partial recv chunks) ──
        self._raw_buf = [b"" for _ in range(self.num_users)]

        # ── Slot store: slot_num → {user_idx: np.array} ────────────────
        #    Once all expected users' packets arrive (or timeout), the
        #    slot is flushed to output_queue.
        self._slots      = {}          # slot_num → {uid: samples}
        self._slot_times = {}          # slot_num → first-arrival time

        # ── Output queue fed to GNU Radio work() ───────────────────────
        self._out_q  = queue.Queue()
        self._out_buf = np.array([], dtype=np.complex64)

        # ── Background receiver thread ──────────────────────────────────
        self._running = True
        self._thread  = threading.Thread(target=self._receiver_loop,
                                         daemon=True)
        self._thread.start()

    # ──────────────────────────────────────────────────────────────────
    #  Background thread — receives from ZMQ, assembles packets, decides
    # ──────────────────────────────────────────────────────────────────
    def _receiver_loop(self):
        while self._running:
            # Poll all sockets with a short timeout
            ready = dict(self.poller.poll(ZMQ_RECV_MS))

            for uid, sock in enumerate(self.sockets):
                if sock not in ready:
                    continue
                try:
                    raw = sock.recv()
                except zmq.Again:
                    continue

                self._raw_buf[uid] += raw

                # Drain complete packets from raw buffer
                while len(self._raw_buf[uid]) >= self.packet_samples * 8:
                    chunk_bytes = self._raw_buf[uid][:self.packet_samples * 8]
                    self._raw_buf[uid] = self._raw_buf[uid][self.packet_samples * 8:]
                    samples = np.frombuffer(chunk_bytes, dtype=np.complex64).copy()
                    self._store_packet(uid, samples)

            # Check for timed-out slots (only one user transmitted)
            self._flush_timed_out_slots()

    def _store_packet(self, uid, samples):
        """Store a complete packet; flush slot if all users present."""
        # Use a simple incrementing slot counter per user
        # We key slots by a tuple approach: find the next open slot for uid
        slot_num = self._find_or_create_slot(uid)

        self._slots[slot_num][uid] = samples
        if slot_num not in self._slot_times:
            self._slot_times[slot_num] = time.time()

        print(f"[SlotCombiner] Slot {slot_num}: User {uid+1} packet stored "
              f"({len(samples)} samples)")

        # If all users have contributed to this slot → output immediately
        if len(self._slots[slot_num]) == self.num_users:
            self._flush_slot(slot_num, reason="COLLISION")

    def _find_or_create_slot(self, uid):
        """Return the earliest open slot_num that doesn't have uid yet."""
        for snum in sorted(self._slots.keys()):
            if uid not in self._slots[snum]:
                return snum
        # No open slot — create a new one
        new_num = max(self._slots.keys(), default=-1) + 1
        self._slots[new_num] = {}
        return new_num

    def _flush_timed_out_slots(self):
        """Flush slots that have been waiting longer than slot_timeout_ms."""
        now = time.time()
        timeout_s = self.slot_timeout_ms / 1000.0

        for snum in list(self._slots.keys()):
            age = now - self._slot_times.get(snum, now)
            if age >= timeout_s:
                self._flush_slot(snum, reason="NO COLLISION (timeout)")

    def _flush_slot(self, slot_num, reason=""):
        """Combine available user samples and push to output queue."""
        packets = self._slots.pop(slot_num, {})
        self._slot_times.pop(slot_num, None)

        if not packets:
            return

        # Add all available user signals (superposition)
        combined = np.zeros(self.packet_samples, dtype=np.complex64)
        for uid, samples in packets.items():
            # Pad or trim to exact packet_samples length
            n = min(len(samples), self.packet_samples)
            combined[:n] += samples[:n]

        users_present = [uid + 1 for uid in packets.keys()]
        print(f"[SlotCombiner] Slot {slot_num} → {reason} | "
              f"Users: {users_present} | Output: {len(combined)} samples")

        self._out_q.put(combined)

    # ──────────────────────────────────────────────────────────────────
    #  GNU Radio work() — feeds output_queue to the stream
    # ──────────────────────────────────────────────────────────────────
    def work(self, input_items, output_items):
        out = output_items[0]
        n_wanted = len(out)

        # Refill internal output buffer from queue
        while len(self._out_buf) < n_wanted:
            try:
                chunk = self._out_q.get_nowait()
                self._out_buf = np.concatenate([self._out_buf, chunk])
            except queue.Empty:
                break

        if len(self._out_buf) == 0:
            # Nothing ready — output silence (zeros) to keep stream alive
            out[:] = np.zeros(n_wanted, dtype=np.complex64)
            return n_wanted

        # Copy as many samples as we have
        n_out = min(n_wanted, len(self._out_buf))
        out[:n_out] = self._out_buf[:n_out]
        self._out_buf = self._out_buf[n_out:]

        # Pad remainder with zeros if needed
        if n_out < n_wanted:
            out[n_out:] = 0

        return n_wanted

    # ──────────────────────────────────────────────────────────────────
    #  Cleanup
    # ──────────────────────────────────────────────────────────────────
    def stop(self):
        self._running = False
        self._thread.join(timeout=1.0)
        self.poller.unregister(sock)   # unregister first
        for sock in self.sockets:
            sock.setsockopt(zmq.LINGER, 0)  # force zero linger at close time too
            sock.close()
        self.ctx.destroy(linger=0)  #  self.ctx.term() # use destroy() not term()
        return True
    

    """
    here you said we are creating a buffer for each user
      but what if we have single buffer for all users and listen to multiple users at same 
      time add the corresponding chunks from each user if they are collided and pass it to 
      the channel instead of packet we will be adding chunk by chunk doesn't it work similar 
      to aloha"""