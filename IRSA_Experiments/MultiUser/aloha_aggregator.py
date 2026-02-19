import zmq
import time
import numpy as np
import threading
from collections import deque

# ─── Configuration ────────────────────────────────────────────────
NUM_USERS        = 3
BASE_PORT        = 49210
RECV_PORT        = 49203
SAMP_RATE        = 768000
ITEM_SIZE        = 8              # gr_complex = 8 bytes
PACKET_SAMPLES   = 34079          # your measured value
PACKET_BYTES     = PACKET_SAMPLES * ITEM_SIZE   # 34079 * 8 = 272632 bytes
PACKET_DURATION  = PACKET_SAMPLES / SAMP_RATE   # ~44.37 ms

print(f"Packet duration:  {PACKET_DURATION*1000:.2f} ms")
print(f"Packet samples:   {PACKET_SAMPLES}")
print(f"Packet bytes:     {PACKET_BYTES}")

# ─── Shared State ─────────────────────────────────────────────────
active_window = deque()
window_lock   = threading.Lock()

user_stats = {
    i: {
        'sent'      : 0,
        'collisions': 0,
        'seq_sent'  : [],
        'seq_coll'  : [],
    }
    for i in range(NUM_USERS)
}
stats_lock = threading.Lock()

context = zmq.Context()

# Output to Channel Model
out_sock = context.socket(zmq.PUB)
out_sock.bind(f"tcp://127.0.0.1:{RECV_PORT}")
time.sleep(0.5)


def check_collision(new_start, new_end, exclude_user):
    with window_lock:
        for pkt in active_window:
            if pkt['user'] == exclude_user:
                continue
            if (new_start < pkt['end']) and (pkt['start'] < new_end):
                return True, pkt['user'], pkt['seq_num']
    return False, None, None


def cleanup_window():
    now = time.time()
    with window_lock:
        while active_window and active_window[0]['end'] < now:
            active_window.popleft()


def accumulate_packet(sock):
    """
    Keep calling sock.recv() and accumulating bytes
    until we have exactly PACKET_BYTES worth of IQ data.
    This converts the raw ZMQ stream into discrete packets.
    """
    buffer = b""

    while len(buffer) < PACKET_BYTES:
        chunk     = sock.recv()
        buffer   += chunk
        remaining = PACKET_BYTES - len(buffer)
        print(f"    [accumulate] got {len(chunk)} bytes, "
              f"total={len(buffer)}/{PACKET_BYTES}, "
              f"remaining={remaining}")
        # Add temporarily inside accumulate loop to see chunk sizes:
        print(f"Chunk size: {len(chunk)} bytes")
        print(f"PACKET_BYTES expected: {PACKET_BYTES}")

    # If we accumulated slightly more than one packet,
    # return exactly one packet and keep the rest
    packet   = buffer[:PACKET_BYTES]
    leftover = buffer[PACKET_BYTES:]
    return packet, leftover


def user_receiver(user_id, pull_port):
    sock = context.socket(zmq.PULL)
    sock.bind(f"tcp://127.0.0.1:{pull_port}")
    print(f"[User {user_id}] listening on port {pull_port}")

    local_seq = 0
    leftover  = b""    # bytes carried over from previous accumulation

    while True:
        # ── Accumulate exactly one packet's worth of IQ data ──────
        buffer = leftover   # start with any leftover from last packet

        while len(buffer) < PACKET_BYTES:
            chunk   = sock.recv()
            buffer += chunk

        # Slice exactly one packet, keep remainder for next round
        packet_data = buffer[:PACKET_BYTES]
        leftover    = buffer[PACKET_BYTES:]

        # ── Record arrival time WHEN packet is complete ────────────
        arrival  = time.time()
        end_time = arrival + PACKET_DURATION
        local_seq += 1

        pkt_entry = {
            'user'   : user_id,
            'seq_num': local_seq,
            'start'  : arrival,
            'end'    : end_time,
            'data'   : packet_data,
        }

        with window_lock:
            active_window.append(pkt_entry)

        print(f"[User {user_id}] PKT #{local_seq:04d} COMPLETE "
              f"({len(packet_data)} bytes) "
              f"t={arrival:.4f} → {end_time:.4f}")

        # Wait for full packet duration before deciding collision
        remaining = PACKET_DURATION - (time.time() - arrival)
        if remaining > 0:
            time.sleep(remaining)

        # ── Collision Decision ─────────────────────────────────────
        collided, other_user, other_seq = check_collision(
            arrival, end_time, exclude_user=user_id
        )

        with window_lock:
            try:
                active_window.remove(pkt_entry)
            except ValueError:
                pass

        cleanup_window()

        with stats_lock:
            if collided:
                user_stats[user_id]['collisions'] += 1
                user_stats[user_id]['seq_coll'].append(local_seq)
                print(f"[User {user_id}] PKT #{local_seq:04d} "
                      f"COLLISION with User {other_user} "
                      f"PKT #{other_seq:04d} — DROPPED")
            else:
                user_stats[user_id]['sent'] += 1
                user_stats[user_id]['seq_sent'].append(local_seq)
                print(f"[User {user_id}] PKT #{local_seq:04d} "
                      f"SUCCESS — forwarding to channel")
                out_sock.send(packet_data)


def stats_reporter():
    while True:
        time.sleep(10)
        print("\n" + "═"*55)
        print(f"{'PURE ALOHA — PER USER STATS':^55}")
        print("═"*55)

        total_sent = 0
        total_coll = 0

        with stats_lock:
            for uid in range(NUM_USERS):
                s   = user_stats[uid]['sent']
                c   = user_stats[uid]['collisions']
                tot = s + c
                tput = s / tot if tot > 0 else 0
                total_sent += s
                total_coll += c

                print(f" User {uid}:  Sent={s:4d}  "
                      f"Collisions={c:4d}  "
                      f"Total={tot:4d}  "
                      f"Throughput={tput:.3f}")

                if user_stats[uid]['seq_coll']:
                    print(f"   Last collided seq#: "
                          f"{user_stats[uid]['seq_coll'][-5:]}")

        grand_total = total_sent + total_coll
        grand_tput  = total_sent / grand_total if grand_total > 0 else 0

        print("─"*55)
        print(f" TOTAL:  Sent={total_sent}  "
              f"Collisions={total_coll}  "
              f"Throughput={grand_tput:.3f}")
        print(f" Theory max Pure ALOHA: {1/(np.e*2):.3f}")
        print("═"*55 + "\n")


# ─── Launch ───────────────────────────────────────────────────────
threads = []

for uid in range(NUM_USERS):
    port = BASE_PORT + uid
    t = threading.Thread(target=user_receiver,
                         args=(uid, port),
                         daemon=True)
    threads.append(t)
    t.start()

t_stats = threading.Thread(target=stats_reporter, daemon=True)
t_stats.start()

print(f"Pure ALOHA aggregator — {NUM_USERS} users")
print(f"Packet duration: {PACKET_DURATION*1000:.2f} ms\n")

for t in threads:
    t.join()