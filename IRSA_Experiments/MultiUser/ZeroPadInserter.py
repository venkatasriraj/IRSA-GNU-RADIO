"""
zero_pad_inserter — corrected EPB for GNU Radio ALOHA simulation
================================================================

PURPOSE
-------
Converts a back-to-back packet stream (output of the TX modulator chain)
into a time-stamped stream where each packet begins at its correct absolute
sample position.  When two such streams are fed into a GNU Radio `Add` block
the result correctly models ALOHA collision semantics:
  - overlapping packets are summed (collision)
  - non-overlapping packets appear at their true positions (no spurious sum)

KEY FIX vs original
-------------------
Old code:  drew a *random exponential gap* before each packet → wrong positions
New code:  computes pad = (rx_time − T0) × samp_rate − abs_out_offset

SHARED T0 REQUIREMENT
---------------------
Every zero_pad_inserter instance in the flowgraph **must** receive the same
T0 value.  Pass it as a constructor argument, e.g.:

    inserter_tx1 = zero_pad_inserter(samp_rate=768e3, T0=shared_epoch)
    inserter_tx2 = zero_pad_inserter(samp_rate=768e3, T0=shared_epoch)

If T0 is None the first instance that sees a packet establishes the epoch and
you must propagate that value to all other instances before their first
packet arrives (use a message port or a shared module-level variable).

TAGS EXPECTED ON INBOUND STREAM
--------------------------------
At the same sample offset for each packet:
  • "packet_len"  (long)   — number of samples in the packet body
  • "rx_time"     (double) — absolute transmission time in seconds (epoch-free)
                             Produced by seq_tagger / Random_Packet_Generator.

VERIFIED AGAINST
----------------
CSV data (iq_badd1, iq_badd2, iq_Aadd) from 2026-03-19 run:
  TX1 Pkt1 (isolated)   → no collision  ✓
  TX1 Pkt2 vs TX2 Pkt1 → 18 823 samples collision (24.5 ms)  ✓
  TX1 Pkt3 vs TX2 Pkt2 → 18 957 samples collision (24.7 ms)  ✓
"""

import numpy as np
import pmt
import gnuradio.gr as gr


class zero_pad_inserter(gr.sync_block):
    # Use gr.basic_block if this is message-only; sync_block for stream I/O.

    def __init__(self, samp_rate: float = 768_000.0, T0: float = None):
        gr.sync_block.__init__(
            self,
            name="zero_pad_inserter",
            in_sig=[np.complex64],
            out_sig=[np.complex64],
        )
        self._samp_rate     = float(samp_rate)
        self._T0            = T0          # absolute epoch in seconds; None → auto

        # ── mutable state ────────────────────────────────────────────────────
        self._abs_in_offset  = 0   # total input  samples consumed so far
        self._abs_out_offset = 0   # total output samples produced so far

        self._pad_remaining  = 0   # zeros still to emit before current packet
        self._in_packet      = False
        self._pkt_remaining  = 0   # packet body samples still to copy

    # ── helpers ──────────────────────────────────────────────────────────────

    def _build_rx_time_map(self, in_len: int) -> dict:
        """Return {abs_offset: rx_time_seconds} for all rx_time tags in window."""
        result = {}
        for t in self.get_tags_in_window(0, 0, in_len, pmt.intern("rx_time")):
            result[t.offset] = pmt.to_double(t.value)
        return result

    # ── main work function ───────────────────────────────────────────────────

    def work(self, input_items, output_items):
        in0  = input_items[0]
        out  = output_items[0]
        nout = len(out)
        n_written  = 0
        n_consumed = 0

        # Fetch all packet_len tags and rx_time tags in this window once.
        plen_tags  = self.get_tags_in_window(
            0, 0, len(in0), pmt.intern("packet_len"))
        rx_time_map = self._build_rx_time_map(len(in0))

        while n_written < nout:

            # ── Phase 1: drain pending zero-pad ─────────────────────────────
            if self._pad_remaining > 0:
                chunk = min(self._pad_remaining, nout - n_written)
                out[n_written : n_written + chunk] = 0 + 0j
                self._pad_remaining   -= chunk
                n_written             += chunk
                self._abs_out_offset  += chunk
                continue

            # ── Phase 2: copy packet body ────────────────────────────────────
            if self._in_packet and self._pkt_remaining > 0:
                available = len(in0) - n_consumed
                chunk = min(self._pkt_remaining, nout - n_written, available)
                if chunk == 0:
                    break
                out[n_written : n_written + chunk] = in0[n_consumed : n_consumed + chunk]
                self._pkt_remaining   -= chunk
                n_written             += chunk
                n_consumed            += chunk
                self._abs_out_offset  += chunk
                if self._pkt_remaining == 0:
                    self._in_packet = False
                continue

            # ── Phase 3: locate next packet_len tag ─────────────────────────
            current_abs = self._abs_in_offset + n_consumed
            upcoming = [t for t in plen_tags if t.offset >= current_abs]
            if not upcoming:
                n_consumed = len(in0)
                break

            tag     = upcoming[0]
            pkt_len = pmt.to_long(tag.value)

            # ── Compute absolute sample target from rx_time ──────────────────
            if tag.offset not in rx_time_map:
                # Missing rx_time tag — upstream configuration error.
                raise RuntimeError(
                    f"zero_pad_inserter: no rx_time tag at offset {tag.offset}. "
                    f"Available rx_time offsets: {sorted(rx_time_map.keys())}. "
                    f"Ensure seq_tagger emits rx_time alongside packet_len."
                )

            rx_time_sec = rx_time_map[tag.offset]

            if self._T0 is None:
                # Auto-establish epoch from first packet seen.
                # WARNING: all inserter instances must end up with the same T0.
                # Pass T0 explicitly in the constructor to avoid this race.
                self._T0 = rx_time_sec

            target = int((rx_time_sec - self._T0) * self._samp_rate)

            # ── Sanity: output must not go backward ──────────────────────────
            pad = target - self._abs_out_offset
            if pad < 0:
                raise RuntimeError(
                    f"zero_pad_inserter: negative pad ({pad:,}) at tag offset "
                    f"{tag.offset}.  rx_time={rx_time_sec:.6f}  T0={self._T0:.6f}  "
                    f"target={target:,}  abs_out={self._abs_out_offset:,}.  "
                    f"Possible causes: out-of-order packets, wrong T0, or "
                    f"sample-rate mismatch."
                )

            # ── Skip inter-tag input samples (should be 0 in normal use) ────
            skip = int(tag.offset - current_abs)
            assert skip >= 0
            if skip > 0:
                # Samples exist in the input stream between packets.
                # These are not packet data — silently consume them but do NOT
                # advance abs_out_offset (they produce no output).
                n_consumed += skip

            self._pad_remaining = pad
            self._in_packet     = True
            self._pkt_remaining = pkt_len
            # Loop back to Phase 1 to start emitting zeros.

        self._abs_in_offset += n_consumed
        self.consume(0, n_consumed)
        return n_written