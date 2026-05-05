import csv

TX_FILE  = "data_tx1.csv"
RX_FILE  = "rx_log.csv"
USER_ID  = 1

# TX packet layout (bytes):
#   [0:4]  preamble  (skip)
#   [4:6]  seq_num   (skip)
#   [6:8]  user_id   (skip)
#   [8:52] payload   ← compare this
#   [52:56] filler   (skip)
TX_PAYLOAD_START = 8
TX_PAYLOAD_END   = 52   # 44 bytes of actual data


def load_tx(path):
    """Returns dict: seq_num -> payload bytes (list of int)"""
    tx = {}
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            if int(row['user_id']) != USER_ID:
                continue
            raw = [int(x, 16) for x in row['data_hex'].split()]
            seq = (raw[4] << 8) | raw[5]
            tx[seq] = raw[TX_PAYLOAD_START:TX_PAYLOAD_END]
    return tx


def load_rx(path):
    """Returns dict: seq_num -> payload bytes (list of int)"""
    rx = {}
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            if int(row['user_id']) != USER_ID:
                continue
            seq = int(row['seq_num'])
            rx[seq] = [int(x, 16) for x in row['payload_hex'].split()]
    return rx


def byte_errors(tx_bytes, rx_bytes):
    """Return number of bit errors between two equal-length byte lists."""
    errors = 0
    for t, r in zip(tx_bytes, rx_bytes):
        errors += bin(t ^ r).count('1')
    return errors


def main():
    tx = load_tx(TX_FILE)
    rx = load_rx(RX_FILE)

    tx_seqs = set(tx.keys())
    rx_seqs = set(rx.keys())

    matched      = sorted(tx_seqs & rx_seqs)
    lost_packets = sorted(tx_seqs - rx_seqs)   # sent but not received
    extra_pkts   = sorted(rx_seqs - tx_seqs)   # received but not in TX log (false detections)

    total_bit_errors = 0
    total_bits       = 0
    errored_packets  = 0

    print(f"\n{'='*55}")
    print(f"  BER / PER Report  —  User {USER_ID}")
    print(f"{'='*55}")
    print(f"  TX packets : {len(tx_seqs)}")
    print(f"  RX packets : {len(rx_seqs)}")
    print(f"  Matched    : {len(matched)}")
    print(f"  Lost       : {len(lost_packets)}  {lost_packets}")
    print(f"  Extra (FD) : {len(extra_pkts)}   {extra_pkts}")
    print(f"{'-'*55}")
    print(f"  {'seq':>5}  {'bit_errors':>10}  {'bits':>6}  {'BER':>10}")
    print(f"{'-'*55}")

    for seq in matched:
        t = tx[seq]
        r = rx[seq]

        # Sanity check lengths match
        compare_len = min(len(t), len(r))
        if len(t) != len(r):
            print(f"  seq={seq}: length mismatch TX={len(t)} RX={len(r)}, comparing {compare_len}B")

        bits   = compare_len * 8
        errors = byte_errors(t[:compare_len], r[:compare_len])

        total_bit_errors += errors
        total_bits       += bits
        if errors > 0:
            errored_packets += 1

        ber_pkt = errors / bits if bits else 0
        print(f"  {seq:>5}  {errors:>10}  {bits:>6}  {ber_pkt:>10.6f}")

    print(f"{'='*55}")

    overall_ber = total_bit_errors / total_bits if total_bits else 0
    # PER = fraction of matched packets that had at least one bit error
    per_matched = errored_packets / len(matched) if matched else 0
    # PER including lost packets (lost = 100% packet error)
    per_total   = (errored_packets + len(lost_packets)) / len(tx_seqs) if tx_seqs else 0

    print(f"  Total bit errors   : {total_bit_errors}")
    print(f"  Total bits compared: {total_bits}")
    print(f"  BER                : {overall_ber:.6f}  ({overall_ber*100:.4f}%)")
    print(f"  PER (matched only) : {per_matched:.6f}  ({per_matched*100:.2f}%)")
    print(f"  PER (incl. lost)   : {per_total:.6f}  ({per_total*100:.2f}%)")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()