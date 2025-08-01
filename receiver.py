import socket

# Initialize UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", 12345))

# Connection setup
def receive_syn():
    request, client_addr = sock.recvfrom(1024)
    if request.decode() == "SYN":
        sock.sendto("SYN-ACK".encode(), client_addr)
        response, _ = sock.recvfrom(1024)
        if response.decode() == "ACK":
            return client_addr

# Data transfer with cumulative ACKs
def receive_data():
    expected_seq_num = 0
    received_data = []

    while True:
        packet, client_addr = sock.recvfrom(1024)
        if packet.decode() == "FIN":
            sock.sendto("ACK".encode(), client_addr)
            break

        seq_num, data = packet.decode().split(":")
        seq_num = int(seq_num)

        if seq_num == expected_seq_num:
            received_data.append(data)
            expected_seq_num += 1
            sock.sendto(str(seq_num).encode(), client_addr)
        else:
            # Send cumulative ACK for the last in-order packet
            sock.sendto(str(expected_seq_num - 1).encode(), client_addr)

# Connection termination
def receive_fin():
    response, client_addr = sock.recvfrom(1024)
    if response.decode() == "FIN-ACK":
        sock.sendto("ACK".encode(), client_addr)

# Example usage
client_addr = receive_syn()
receive_data()
receive_fin()
sock.close()
