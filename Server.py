import socket
import select
import struct
import sys

def handle_client(client_socket):
    header = client_socket.recv(6)
    if not header:
        return False

    msg_type, n = struct.unpack('!HI', header)
    if msg_type != 1:
        return False

    client_socket.sendall(struct.pack('!H', 2))

    for _ in range(n):
        req_header = client_socket.recv(6)
        _, length = struct.unpack('!HI', req_header)
        data = client_socket.recv(length).decode()
        reversed_data = data[::-1]
        res_message = struct.pack('!HI', 4, length) + reversed_data.encode()
        client_socket.sendall(res_message)

    return True

def main(server_ip, server_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)
    print(f"Server listening on {server_ip}:{server_port}")

    inputs = [server_socket]
    while True:
        readable, _, _ = select.select(inputs, [], [])
        for s in readable:
            if s is server_socket:
                client_socket, addr = server_socket.accept()
                inputs.append(client_socket)
            else:
                if not handle_client(s):
                    inputs.remove(s)
                    s.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python server.py <server_ip> <server_port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    main(server_ip, server_port)
