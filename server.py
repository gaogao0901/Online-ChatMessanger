import socket
import threading

clients = []

def handle_client(client_socket, addr):
    print(f"Connection from {addr} has been established!")
    
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                broadcast(message, client_socket)
            else:
                break
        except:
            break

    print(f"Connection from {addr} has been closed.")
    client_socket.close()
    clients.remove(client_socket)

def broadcast(message, client_socket):
    for client in clients:
        if client != client_socket:
            try:
                client.send(message.encode('utf-8'))
            except:
                client.close()
                clients.remove(client)

def main():
    host = '127.0.0.1'  # Server address
    port = 12345  # Server port

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()

    print("Server is listening...")
    
    while True:
        client_socket, addr = server_socket.accept()
        clients.append(client_socket)
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()

if __name__ == "__main__":
    main()
