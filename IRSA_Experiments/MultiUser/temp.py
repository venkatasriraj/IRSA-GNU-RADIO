import numpy as np
from gnuradio import gr
import pmt

class blk(gr.sync_block):
    """
    Energy-Based Tag Deduplicator for ALOHA Add-Block Channel
    ----------------------------------------------------------
    Takes THREE inputs:
      in0 = Add block output  (combined signal  → passed to output)
      in1 = User 1 stream     (energy monitor only, not passed out)
      in2 = User 2 stream     (energy monitor only, not passed out)

    Detects which users are ACTUALLY transmitting based on signal
    energy, then emits clean tags accordingly.
    """

    # Threshold below which a stream is considered silent
    ENERGY_THRESHOLD = 1e-6

    def __init__(self, packet_samples=34079):
        gr.sync_block.__init__(
            self,
            name="aloha_tag_dedup",
            in_sig=[np.complex64,   # in0: Add output  → goes to out
                    np.complex64,   # in1: User 1 raw stream
                    np.complex64],  # in2: User 2 raw stream
            out_sig=[np.complex64]
        )
        self.packet_samples = packet_samples
        self.set_tag_propagation_policy(gr.TPP_DONT)  # block all auto tags

    def _stream_has_energy(self, samples):
        """Returns True if stream has actual packet data (non-silence)."""
        power = np.mean(np.abs(samples) ** 2)
        return power > self.ENERGY_THRESHOLD

    def work(self, input_items, output_items):
        combined = input_items[0]   # Add block output
        user1    = input_items[1]   # User 1 raw
        user2    = input_items[2]   # User 2 raw

        output_items[0][:] = combined  # pass combined signal through

        # ── Get packet_len tags from the combined stream ────────────
        tags = self.get_tags_in_window(
            0, 0, len(combined), pmt.intern("packet_len")
        )

        for tag in tags:
            offset = tag.offset

            # Window of samples around this tag in each user stream
            # (relative to this work() call's starting offset)
            abs_start = self.nitems_written(0)
            rel_offset = offset - abs_start

            # Slice packet window from each user's stream
            start = rel_offset
            end   = min(rel_offset + self.packet_samples, len(user1))

            u1_active = self._stream_has_energy(user1[start:end])
            u2_active = self._stream_has_energy(user2[start:end])

            # ── Decision ───────────────────────────────────────────
            if u1_active and u2_active:
                # COLLISION — emit single packet_len tag
                # RX will attempt decode → CRC will fail → correct
                self.add_item_tag(0, offset, tag.key, tag.value)
                print(f"[TagDedup] offset={offset} → COLLISION "
                      f"(both users active) — 1 tag emitted, CRC will fail")

            elif u1_active:
                # Only User 1 — emit clean tags
                self.add_item_tag(0, offset, tag.key, tag.value)
                self._copy_user_tags(0, offset)
                print(f"[TagDedup] offset={offset} → User 1 only — clean")

            elif u2_active:
                # Only User 2 — emit clean tags
                self.add_item_tag(0, offset, tag.key, tag.value)
                self._copy_user_tags(1, offset)
                print(f"[TagDedup] offset={offset} → User 2 only — clean")

            else:
                # Neither active — silence, no tag needed
                print(f"[TagDedup] offset={offset} → silence, tag dropped")

        return len(combined)

    def _copy_user_tags(self, port, offset):
        """Copy user_id and seq_num tags from a specific input port."""
        for key in ["user_id", "seq_num", "tx_time"]:
            tags = self.get_tags_in_window(
                port, 0,
                len(self.input_items[port]),   # full window
                pmt.intern(key)
            )
            for t in tags:
                if t.offset == offset:
                    self.add_item_tag(0, offset, t.key, t.value)
"""
### Updated Flowgraph

f_samp1 ──► iq_logger ──┬──────────────────────────────► in1 (energy monitor)
                         │                                      │
                         ├──► Add ──► in0 [aloha_tag_dedup] ──► out ──► ZMQ PUB
                         │                    ▲
f_samp2 ──► iq_logger ──┴──────────────────► in2 (energy monitor)


### What Changes Per Scenario

Slot where only User 1 transmits:
  u1_active = True  (high energy)
  u2_active = False (near-zero energy)
  → emit packet_len + user_id=1 + seq_num=N
  → RX decodes → CRC passes ✓

Slot where only User 2 transmits:
  u1_active = False
  u2_active = True
  → emit packet_len + user_id=2 + seq_num=M
  → RX decodes → CRC passes ✓

Slot where both transmit (collision):
  u1_active = True
  u2_active = True
  → emit single packet_len only (no user identity)
  → RX attempts decode → CRC FAILS → packet lost ✓

Silence slot:
  u1_active = False
  u2_active = False
  → no tag emitted ✓
"""

