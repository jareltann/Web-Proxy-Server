import socket
import threading
import queue
import os
from datetime import datetime
import time

# Constants
BUFFER_SIZE = 8192
HOST = '127.0.0.1'
PORT = 8081
NUM_THREADS = 10  # Number of worker threads

# Function to parse HTTP headers
def parse_headers(headers):
    header_dict = {}
    for header in headers:
        parts = header.split(":", 1)
        if len(parts) == 2:
            header_dict[parts[0].strip()] = parts[1].strip()
    return header_dict

# Function to handle client requests
def handle_client(client_socket):
    try:
        # Receive the request message from the client
        message = client_socket.recv(1024).decode()
        if not message:
            raise ValueError("Empty Request")
        
        # Extract the path of the requested file
        request_line = message.split('\r\n')[0]
        parts = request_line.split()
        if len(parts) != 3 or not parts[1].startswith("/") or not parts[2].startswith("HTTP/"):
            raise IOError("Bad Request")
        
        method, filename, protocol = parts

        # Parse headers
        headers = message.split('\r\n')[1:]
        header_dict = parse_headers(headers)

        # Debugging: print the parsed headers
        print("Headers: {}".format(header_dict))

        # Check for unsupported method
        if method != "GET":
            raise IOError("Bad Request")

        # Open the requested file
        filepath = filename[1:]
        if not os.path.isfile(filepath):
            raise IOError("Not Found")

        # Check if file access is allowed
        if not os.access(filepath, os.R_OK):
            raise IOError("Forbidden")

        # Check for If-Modified-Since header
        ims_header = header_dict.get("If-Modified-Since", None)
        if ims_header:
            try:
                ims_time = time.mktime(datetime.strptime(ims_header, '%a, %b %d %H:%M:%S %Y %Z').timetuple())
                file_mod_time = os.path.getmtime(filepath)
                if ims_time >= file_mod_time:
                    # Send 304 Not Modified response
                    print("304 Not Modified")
                    response_header = "HTTP/1.1 304 Not Modified\r\n\r\n"
                    client_socket.send(response_header.encode())
                    client_socket.close()
                    return
            except Exception as e:
                print("Error parsing If-Modified-Since header: {}".format(e))

        # Read the file content
        with open(filepath, "rb") as file:
            outputdata = file.read()

        # Send HTTP response header
        response_header = "HTTP/1.1 200 OK\r\n"
        response_header += "Content-Length: {}\r\n".format(len(outputdata))
        response_header += "Content-Type: text/html\r\n\r\n"
        client_socket.send(response_header.encode())

        # Send the content of the requested file to the client
        client_socket.send(outputdata)

    except IOError as e:
        if "Forbidden" in str(e):
            # Send response message for forbidden access
            error_message = "HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n"
            error_message += "<html><body><h1>403 Forbidden</h1></body></html>"
            client_socket.send(error_message.encode())
        elif "Bad Request" in str(e):
            # Send response message for bad request
            error_message = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n"
            error_message += "<html><body><h1>400 Bad Request</h1></body></html>"
            client_socket.send(error_message.encode())           
        elif "Not Found" in str(e):
            # Send response message for file not found
            error_message = "HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n"
            error_message += "<html><body><h1>404 Not Found</h1></body></html>"
            client_socket.send(error_message.encode())
        else:
            # Send response message for other IO errors
            error_message = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n"
            error_message += "<html><body><h1>500 Internal Server Error</h1><p>{}</p></body></html>".format(e)
            client_socket.send(error_message.encode())
    except Exception as e:
        # Send response message for other errors
        error_message = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n"
        error_message += "<html><body><h1>500 Internal Server Error</h1><p>{}</p></body></html>".format(e)
        client_socket.send(error_message.encode())
    finally:
        # Close the client socket
        client_socket.close()

def worker():
    while True:
        client_socket = request_queue.get()
        if client_socket is None:
            break
        handle_client(client_socket)
        request_queue.task_done()

def main():
    # Create a socket to listen for incoming client connections
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Web server listening on port {PORT}...")

    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connection from {client_address}")
        request_queue.put(client_socket)

if __name__ == "__main__":
    request_queue = queue.Queue()
    main()
