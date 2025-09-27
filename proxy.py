import socket
import threading

# Constants
BUFFER_SIZE = 8192  # The size of the buffer for receiving data
PROXY_PORT = 8888   # The port the proxy server will listen on

# Function to handle client requests
def handle_client(client_socket):
    try:
        # Receive request from the client
        request = client_socket.recv(BUFFER_SIZE)
        print("Received request from client:\n", request.decode())
        
        # Parse the request to extract the URL
        request_lines = request.decode().split('\n')
        url = request_lines[0].split()[1]
        
        # Extract the host and port from the URL
        http_pos = url.find("://")
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos+3):]
        
        # Find the position of the port (if specified)
        port_pos = temp.find(":")
        
        # Find the position of the path in the URL
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)
        
        webserver = ""
        port = -1
        if (port_pos == -1 or webserver_pos < port_pos):
            # Default to port 80 if no port is specified
            port = 80
            webserver = temp[:webserver_pos]
        else:
            # Extract the specified port
            port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
            webserver = temp[:port_pos]
        
        # Create a socket to connect to the web server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((webserver, port))
        
        # Forward the client's request to the web server
        server_socket.sendall(request)
        
        while True:
            # Receive response from the web server
            response = server_socket.recv(BUFFER_SIZE)
            if len(response) > 0:
                # Forward the response to the client
                client_socket.send(response)
            else:
                break
        
        # Close the server socket
        server_socket.close()
    except Exception as e:
        print(f"Error handling client request: {e}")
    finally:
        # Close the client socket
        client_socket.close()

def main():
    # Create a socket to listen for incoming client connections
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_socket.bind(('127.0.0.1', PROXY_PORT))
    proxy_socket.listen(5)
    print(f"Proxy server listening on port {PROXY_PORT}...")
    
    while True:
        client_socket, client_address = proxy_socket.accept()
        print(f"Connection from {client_address}")
        # Create a new thread to handle the client request
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()
