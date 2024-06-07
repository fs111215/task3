import socket
import struct
import random
import sys


#读取ASCII文件内容
def read_ascii_file(filepath):
    with open(filepath, 'r') as file:
        return file.read()

#将文件内容分割成多个数据块
def split_file_content(content, lmin, lmax):
    blocks = []
    start = 0
    while start < len(content):
        length = random.randint(lmin, lmax)
        blocks.append(content[start:start + length])
        start += length
    return blocks

#发送Initialization报文
def send_initialization(client_socket, n):
    message = struct.pack('!HI', 1, n)
    try:
        client_socket.sendall(message)
    except socket.error:
        print("Connection Error")
        sys.exit(1)

#发送ReverseRequest报文
def send_reverse_request(client_socket, data):
    length = len(data)
    message = struct.pack('!HI', 3, length) + data.encode()
    client_socket.sendall(message)

#接收ReverseAnswer报文
def receive_reverse_answer(client_socket):
    header = client_socket.recv(6)
    if not header:
        return None
    _, length = struct.unpack('!HI', header)
    data = client_socket.recv(length)
    return data.decode()

#主函数
def main(server_ip, server_port, filepath, lmin, lmax):
    try:
        content = read_ascii_file(filepath) #读取文件内容
    except FileNotFoundError:
        print("File error")
        sys.exit(1)

    blocks = split_file_content(content, lmin, lmax) #将文件内容分割成多个数据块
    n = len(blocks) #数据块数

    #创建客户端套接字并连接服务器
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, server_port))
    except socket.gaierror:
        print("Error: Invalid IP address.") #检查服务器IP地址是否有效
        sys.exit(1)
    except OverflowError:
        print("Error: Port number must be between 0 and 65535.") #检查服务器端口Port
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while connecting: {e}")
        sys.exit(1)

    send_initialization(client_socket, n) #发送Initialization报文，并等待服务器回复
    response = client_socket.recv(2)  #接收agree消息
    if not response:
        print("Failed to receive agree message from server")
        client_socket.close()
        return

    reversed_content = []

    #逐个发送数据块并接收反转后的结果
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

    #将反转后的数据块写入到文件中
    with open('reversed_output.txt', 'w') as output_file:
        output_file.write(''.join(reversed_content))


if __name__ == "__main__":
    #检查命令行参数是否正确
    if len(sys.argv) != 6:
        print("Usage: python client.py <server_ip> <server_port> <file_path> <lmin> <lmax>")
        sys.exit(1)

    try: #鲁棒性
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
