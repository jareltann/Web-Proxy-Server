import socket
import random
import time

# Constants
INIT_CWND = 1
WINDOW_SIZE = 10  # Flow control: the receiver's advertised window size
TIMEOUT = 1
LOSS_PROBABILITY = 0.2

# Helper functions for packet loss simulation
def simulate_loss():
    return random.random() < LOSS_PROBABILITY

# Initialize UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(TIMEOUT)

# Connection setup
def send_syn():
    packet = "SYN"
    sock.sendto(packet.encode(), (server_ip, server_port))
    response, _ = sock.recvfrom(1024)
    if response.decode() == "SYN-ACK":
        sock.sendto("ACK".encode(), (server_ip, server_port))

# Data transfer with flow and congestion control
def send_data(data):
    base = 0
    next_seq_num = 0
    cwnd = INIT_CWND  # Congestion window starts with 1
    ssthresh = 8  # Slow start threshold

    while base < len(data):
        while next_seq_num < base + min(cwnd, WINDOW_SIZE) and next_seq_num < len(data):
            packet = f"{next_seq_num}:{data[next_seq_num]}"
            if not simulate_loss():
                sock.sendto(packet.encode(), (server_ip, server_port))
            next_seq_num += 1

        try:
            ack, _ = sock.recvfrom(1024)
            ack_num = int(ack.decode())
            base = ack_num + 1
            if cwnd < ssthresh:
                cwnd *= 2  # Slow start
            else:
                cwnd += 1  # Congestion avoidance
        except socket.timeout:
            ssthresh = cwnd // 2
            cwnd = 1  # Congestion control: reset to slow start
            for seq_num in range(base, next_seq_num):
                packet = f"{seq_num}:{data[seq_num]}"
                if not simulate_loss():
                    sock.sendto(packet.encode(), (server_ip, server_port))

# Connection termination
def send_fin():
    sock.sendto("FIN".encode(), (server_ip, server_port))
    response, _ = sock.recvfrom(1024)
    if response.decode() == "ACK":
        sock.sendto("FIN-ACK".encode(), (server_ip, server_port))

# Example usage
server_ip = "127.0.0.1"
server_port = 12345

send_syn()
send_data(["Hello", "World", "This", "is", "a", "test", "to", "see", "if", "you", "pass",
           "or", "fail", "CMPT", "371", "for", "the", "summer", "sem", "don't", "cry"])
send_fin()
sock.close()
