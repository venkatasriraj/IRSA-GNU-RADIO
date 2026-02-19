import numpy as np 
import sys 

def read_packets(filename): 
    """Read packets from binary file - 2 byte header version""" 
    packets = [] 

    with open(filename, 'rb') as f: 
        packet_num = 1 
        while True: 
            # Read header: 2 bytes length only 
            header = np.fromfile(f, dtype=np.uint8, count=2) 
            if len(header) < 2: 
                break 

            # Calculate length (Little Endian)
            length = header[0] | (header[1] << 8) 

            # Validate expected packet size 
            if length != 52: 
                print(f"Warning: Expected 52 bytes, got {length} at packet {packet_num}") 

            # Read data 
            data = np.fromfile(f, dtype=np.uint8, count=length) 
            if len(data) < length: 
                print(f"Warning: Truncated packet {packet_num}") 
                break 

            packets.append({ 
                'packet_num': packet_num, 
                'length': length, 
                'data': data 
            }) 

            print(f"Packet #{packet_num}: {length} bytes") 
            print(f"  Hex: {' '.join(f'{b:02x}' for b in data[:32])}") 
            
            if length > 32: 
                print(f"  ... ({length - 32} more bytes)") 

            packet_num += 1 

    return packets 

if __name__ == "__main__": 
    if len(sys.argv) < 2: 
        print("Usage: python read_packets.py <session_file.bin>") 
        sys.exit(1) 

    packets = read_packets(sys.argv[1]) 
    print(f"\nTotal packets read: {len(packets)}")