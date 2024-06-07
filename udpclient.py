import socket
import struct
import time
import statistics
import sys
VERSION = b'\x02'
SYN = 'SYN'
FIN = 'FIN'
ACK = 'ACK'
SYN_ACK = 'SYN-ACK'
FIN_ACK = 'FIN-ACK'
END_ACK = 'END-ACK'


class Client:

    def __init__(self, server_ip, server_port):
        try:
            socket.inet_aton(server_ip)  # 检查服务器IP地址是否有效
        except socket.error:
            print("Invalid IP address")
            sys.exit(1)

        try:
            server_port = int(server_port)
            if not (0 < server_port < 65536):
                print("Server port must be an integer between 1 and 65535")
                sys.exit(1)
        except ValueError:
            print("Invalid port number")
            sys.exit(1)

        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #创建UDP套接字
        self.seq_no = 0
        self.rtt_times = []
        self.start_time = None
        self.end_time = None
        self.sent_packets = 0

    def send_packet(self,  data): #发送数据包
        if data not in [ACK, SYN, SYN_ACK, FIN, FIN_ACK]:
            self.seq_no += 1 #如果数据类型不是以上类型，则序列号才加1
        else:
            self.seq_no = 0
        request_time = time.strftime("%H:%M:%S", time.localtime())
        packet = struct.pack('!Hc8s192s', self.seq_no, VERSION, request_time.encode(), data.encode()) #将数据打包成二进制格式
        self.socket.sendto(packet, (self.server_ip, self.server_port))

    def send_request(self, data): #发送请求报文
        self.send_packet(data) #调用发送数据包的方法发送请求

        for attempt in range(3):  # 最多重传两次，即最多发送三次
            start_time = time.time() #记录发送数据包的开始时间
            self.sent_packets += 1 #记录已发送的数据包的数量

            try:
                self.socket.settimeout(0.1)  # 设置超时时间为100ms
                response_packet, _ = self.socket.recvfrom(2048) #接收服务器返回的响应数据包
                end_time = time.time() #记录接收响应数据包的结束时间
                rtt = (end_time - start_time) * 1000  # 计算往返时延（毫秒）
                self.rtt_times.append(rtt) #将rtt存到列表中
                seq_no, ver, server_time, _ = struct.unpack('!Hc8s192s', response_packet)
                server_time = server_time.decode().strip('\x00')
                print(f"Sequence no: {seq_no}, Server IP: {self.server_ip}, Server Port: {self.server_port}, RTT: {rtt:.2f} ms, Server Time: {server_time}")
                break  # 成功接收响应报文后退出循环
            except socket.timeout:
                print(f"Sequence no: {self.seq_no}, Request timed out (Attempt {attempt + 1})") #超时重传

        # 记录服务器响应时间的开始时间和结束时间
        if self.start_time is None:
            self.start_time = time.time()
        self.end_time = time.time()

    def run(self):
        # 模拟TCP连接建立过程（三次握手）
        print("Establishing connection...")
        self.send_packet(SYN)
        try:
            self.socket.settimeout(1)  # 设置超时时间为1秒
            response_packet, _ = self.socket.recvfrom(2048) #接收服务器返回的响应数据包

            seq_no, ver, server_time, content = struct.unpack('!Hc8s192s', response_packet)
            content = content.decode().strip('\x00')
            if content == SYN_ACK:
                print("Connection established.") #建立连接成功
                self.send_packet(ACK) #发送ACK确认连接
            else:
                print("Failed to establish connection.") #连接建立失败
                return
        except socket.timeout:
            print("Connection establishment timed out.") #连接建立超时
            return
        except socket.error:
            print("Connection Error") #连接错误
            sys.exit(1)

        # 发送请求报文
        while self.seq_no < 12: #循环发送请求报文，直到序列号到12
            data = 'A' * 192  # 其他内容，用'A'填充
            self.send_request(data)

        # 模拟连接释放过程（四次挥手）
        print("Releasing connection...")
        self.send_packet(FIN)
        try:
            self.socket.settimeout(1)  # 设置超时时间为1秒
            response_packet, _ = self.socket.recvfrom(2048) #接收服务器返回的响应数据包
            seq_no, ver, server_time, content = struct.unpack('!Hc8s192s', response_packet)
            content = content.decode().strip('\x00')
            if content == FIN_ACK: #这里将服务器端发出的FIN和ACK合并了，便于区分不同时刻报文的含义。在这里表示连接释放成功
                print("Connection released.")
                self.send_packet(END_ACK) #确认连接释放
            else:
                print("Failed to release connection.")
        except socket.timeout:
            print("Connection release timed out.")

        self.socket.close() #关闭套接字

        # 输出总结信息
        received_packets = len(self.rtt_times) #接收到的数据包数量
        lost_packets = self.sent_packets - received_packets #丢失的数据包数量
        loss_rate = (lost_packets / self.sent_packets) * 100 if self.sent_packets > 0 else 0 #丢包率
        max_rtt = max(self.rtt_times) if self.rtt_times else 0 #最大往返时间
        min_rtt = min(self.rtt_times) if self.rtt_times else 0 #最小往返时间
        avg_rtt = statistics.mean(self.rtt_times) if self.rtt_times else 0 #平均往返时间
        rtt_stddev = statistics.stdev(self.rtt_times) if len(self.rtt_times) > 1 else 0 #往返时间标准差
        server_response_time = self.end_time - self.start_time if self.start_time is not None else 0 #服务器响应时间

        print("【Summary】")
        print(f"Sent UDP packets: {self.sent_packets}")
        print(f"Received UDP packets: {received_packets}")
        print(f"Packet loss rate: {loss_rate:.2f}%")
        print(f"Max RTT: {max_rtt:.2f} ms")
        print(f"Min RTT: {min_rtt:.2f} ms")
        print(f"Average RTT: {avg_rtt:.2f} ms")
        print(f"RTT standard deviation: {rtt_stddev:.2f} ms")
        print(f"Server response time: {server_response_time:.2f} seconds")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python Client.py <server_ip> <server_port>")
        sys.exit(1)

    server_ip = sys.argv[1] #通过命令行的形式获取IP地址
    server_port = int(sys.argv[2]) #获取服务器端口号
    client = Client(server_ip, server_port)
    client.run()
