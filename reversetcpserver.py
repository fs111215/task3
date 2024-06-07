import socket
import select
import struct
import sys

def handle_client(client_socket):
    #接收客户端发送的消息头，消息头包含消息类型和数据块数
    header = client_socket.recv(6)
    if not header:
        return False
    #解析消息头，获取消息类型和数据块数
    msg_type, n = struct.unpack('!HI', header)
    #检查报文类型是否为1（Initialization报文）
    if msg_type != 1:
        return False

    #向客户端发送确认消息，报文类型为2（Agree报文）
    client_socket.sendall(struct.pack('!H', 2))

    #循环处理客户端发送的数据请求
    for _ in range(n):
        req_header = client_socket.recv(6) #接收请求头，请求头包含消息类型和数据长度
        _, length = struct.unpack('!HI', req_header)
        data = client_socket.recv(length).decode() #接收请求数据，并解码为字符串
        reversed_data = data[::-1] #对请求数据进行反转处理

        #构造响应报文，报文类型为4（ReverseAnswer报文），包含反转后的数据和长度
        res_message = struct.pack('!HI', 4, length) + reversed_data.encode()
        client_socket.sendall(res_message)

    return True

def main(server_ip, server_port):
    #创建服务器套接字并绑定IP地址和端口
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)
    print(f"Server listening on {server_ip}:{server_port}")

    #用于select的输入列表，包含服务器套接字
    inputs = [server_socket]
    while True:
        #使用select监听可读事件
        readable, _, _ = select.select(inputs, [], [])
        for s in readable:
            if s is server_socket: #如果是服务器套接字，表示有新的连接请求
                client_socket, addr = server_socket.accept() #接受客户端连接
                inputs.append(client_socket) #将客户端套接字添加到输入列表中，以便下次select监听
            else:
                #处理客户端请求
                if not handle_client(s): #如果处理失败，关闭客户端套接字并从输入列表中移除
                    inputs.remove(s)
                    s.close()

if __name__ == "__main__":
    if len(sys.argv) != 3: #检查命令行参数是否正确
        print("Usage: python server.py <server_ip> <server_port>")
        sys.exit(1)

    #从命令行参数中获取服务器IP地址和Port端口号
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    main(server_ip, server_port)
