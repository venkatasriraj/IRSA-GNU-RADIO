import base64
import re

def flexible_decode(input_file, output_file):
    with open(input_file, 'r') as f:
        content = f.read()

    # 1. Find the Base64 content between the preamble ']' and the footer '%UUU'
    # This regex looks for the first ']' and captures everything until '%UUU'
    match = re.search(r'\](.*?)%UUU', content, re.DOTALL)
    
    if match:
        b64_string = match.group(1).strip()
        try:
            # 2. Decode the data
            decoded_data = base64.b64decode(b64_string)
            
            # 3. Write to file
            with open(output_file, 'wb') as f_out:
                f_out.write(decoded_data)
            print(f"Success! Decoded content: {decoded_data.decode('utf-8')}")
        except Exception as e:
            print(f"Error decoding Base64: {e}")
    else:
        print("Could not find valid data between markers.")

flexible_decode('output.tmp', 'decoded.txt')