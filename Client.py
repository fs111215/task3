import socket
import struct
import random
import sys


def read_ascii_file(filepath):
    with open(filepath, 'r') as file:
        return file.read()


def split_file_content(content, lmin, lmax):
    blocks = []
    start = 0
    while start < len(content):
        length = random.randint(lmin, lmax)
        blocks.append(content[start:start + length])
        start += length
    return blocks


def send_initialization(client_socket, n):
    message = struct.pack('!HI', 1, n)
    try:
        client_socket.sendall(message)
    except socket.error:
        print("Connection Error")
        sys.exit(1)


def send_reverse_request(client_socket, data):
    length = len(data)
    message = struct.pack('!HI', 3, length) + data.encode()
    client_socket.sendall(message)


def receive_reverse_answer(client_socket):
    header = client_socket.recv(6)
    if not header:
        return None
    _, length = struct.unpack('!HI', header)
    data = client_socket.recv(length)
    return data.decode()


def main(server_ip, server_port, filepath, lmin, lmax):
    try:
        content = read_ascii_file(filepath)
    except FileNotFoundError:
        print("File error")
        sys.exit(1)

    blocks = split_file_content(content, lmin, lmax)
    n = len(blocks)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, server_port))
    except socket.gaierror:
        print("Error: Invalid IP address.")
        sys.exit(1)
    except OverflowError:
        print("Error: Port number must be between 0 and 65535.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while connecting: {e}")
        sys.exit(1)

    send_initialization(client_socket, n)
    response = client_socket.recv(2)  # Receive agree message
    if not response:
        print("Failed to receive agree message from server")
        client_socket.close()
        return

    reversed_content = []

    for i, block in enumerate(blocks):
        send_reverse_request(client_socket, block)
        reversed_block = receive_reverse_answer(client_socket)
        if reversed_block is None:
            print(f"Failed to receive reversed block {i + 1} from server")
            client_socket.close()
            return
        print(f"Block {i + 1}: {reversed_block}")
        reversed_content.append(reversed_block)

    client_socket.close()

    with open('reversed_output.txt', 'w') as output_file:
        output_file.write(''.join(reversed_content))


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python client.py <server_ip> <server_port> <file_path> <lmin> <lmax>")
        sys.exit(1)

    try:
        server_ip = sys.argv[1]
        server_port = int(sys.argv[2])
        file_path = sys.argv[3]
        lmin = int(sys.argv[4])
        lmax = int(sys.argv[5])
    except ValueError:
        print("Error: Invalid type for server_port, lmin, or lmax. They must be integers.")
        sys.exit(1)

    if lmax < lmin:
        print("Error:lmax < lmin")
        sys.exit(1)

    if lmin <= 0:
        print("Error:lmin <= 0")
        sys.exit(1)

    main(server_ip, server_port, file_path, lmin, lmax)
