from socket import *
import os
from datetime import datetime
import time

# Create a socket
serverSocket = socket(AF_INET, SOCK_STREAM)

# Prepare a server socket
serverPort = 8081  # You can replace this with the desired port number
serverSocket.bind(('127.0.0.1', serverPort))
serverSocket.listen(5)

#authorized_users = ["user1","user2","user3","user4","Kailun"]  # Example list of authorized users
#max_users = 5  # Example maximum number of authorized users (this is arbitrary for this example)

def parse_headers(headers):
    header_dict = {}
    for header in headers:
        parts = header.split(":", 1)
        if len(parts) == 2:
            header_dict[parts[0].strip()] = parts[1].strip()
    return header_dict

while True:
    # Establish the connection
    print('Ready to serve...')
    connectionSocket, addr = serverSocket.accept()
    
    try:
        # Receive the request message from the client
        message = connectionSocket.recv(1024).decode()
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
       
#        if "Invalid-Header" in header_dict:
 #           raise ValueError("Bad Request")


        # Check for valid username
  #     if username not in authorized_users:
   #         raise IOError("Forbidden")
    #    if len(authorized_users) > max_users:
     #       raise IOError("Forbidden")



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
                    connectionSocket.send(response_header.encode())
                    connectionSocket.close()
                    continue
            except Exception as e:
                print("Error parsing If-Modified-Since header: {}".format(e))

        # Read the file content
        with open(filepath, "rb") as file:
            outputdata = file.read()
            file.close()

         # check for forbidden 403   
        if filename == '/forbidden.html':
            raise IOError("Forbidden")
        
        # Send HTTP response header
        else:
            response_header = "HTTP/1.1 200 OK\r\n"
            response_header += "Content-Length: {}\r\n".format(len(outputdata))
            response_header += "Content-Type: text/html\r\n\r\n"
            connectionSocket.sendall(response_header.encode())

            #Send the content of the requested file to the client
            connectionSocket.sendall(outputdata)



    except IOError as e:
        if "Forbidden" in str(e):
            # Send response message for forbidden access
            error_message = "HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n"
            error_message += "<html><body><h1>403 Forbidden</h1></body></html>"
            connectionSocket.sendall(error_message.encode())
        elif "Bad Request" in str(e):
            # Send response message for bad request
            error_message = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n"
            error_message += "<html><body><h1>400 Bad Request</h1></body></html>"
            connectionSocket.sendall(error_message.encode())           
        elif "Not Found" in str(e):
            # Send response message for file not found
            error_message = "HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n"
            error_message += "<html><body><h1>404 Not Found</h1></body></html>"
            connectionSocket.sendall(error_message.encode())
        else:
            # Send response message for other IO errors
            error_message = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n"
            error_message += "<html><body><h1>500 Internal Server Error</h1><p>{}</p></body></html>".format(e)
            connectionSocket.send(error_message.encode())
    except Exception as e:
        # Send response message for other errors
        error_message = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n"
        error_message += "<html><body><h1>500 Internal Server Error</h1><p>{}</p></body></html>".format(e)
        connectionSocket.send(error_message.encode())
    finally:
        # Close the client socket
        connectionSocket.close()
