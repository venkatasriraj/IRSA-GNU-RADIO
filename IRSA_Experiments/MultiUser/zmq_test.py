"""
import zmq, numpy as np, time

ctx = zmq.Context()
sock = ctx.socket(zmq.SUB)
sock.connect("tcp://127.0.0.1:49203")  # ← your channel output address
sock.setsockopt(zmq.SUBSCRIBE, b"")    # subscribe to all messages

print("Listening for 10 seconds...")
start = time.time()
count = 0
while time.time() - start < 100:
    try:
        data = sock.recv(flags=zmq.NOBLOCK)
        samples = np.frombuffer(data, dtype=np.complex64)
        power = np.mean(np.abs(samples)**2)
        count += 1
        print(f"Received message {count}: "
              f"{len(samples)} samples, power={power:.4f}")
    except zmq.Again:
        time.sleep(0.01)

print(f"Total messages received: {count}")
"""

import zmq
import numpy as np
import time

context = zmq.Context()
sock = context.socket(zmq.SUB)
sock.connect("tcp://127.0.0.1:49203")
sock.setsockopt(zmq.SUBSCRIBE, b"")   # subscribe to all messages

print("Listening for 10 seconds...")
start = time.time()
count = 0
total_samples = 0

while time.time() - start < 10:
    if sock.poll(100):                 # wait up to 100ms
        data = sock.recv()
        samples = np.frombuffer(data, dtype=np.complex64)
        count += 1
        total_samples += len(samples)
        print(f"  msg {count}: {len(samples)} samples received")

print(f"Total messages: {count}, Total samples: {total_samples}")
sock.close()
context.term()