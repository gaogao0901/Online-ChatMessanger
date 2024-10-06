import socket, threading, time, secrets

class TCPServer:
    room_members_map = {}  # {room_name : [token, token, ...]}
    clients_map = {}  # {token : [client_address, room_name, username, host]}

    def __init__(self, address, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((address, port))  # サーバをバインド
        self.HEADER_MAX_BYTE, self.TOKEN_MAX_BYTE = 32, 255

    def tcp_main(self):
        while True:
            try:
                self.sock.listen()
                conn, client_addr = self.sock.accept()  # クライアント接続を受け入れ
                data = conn.recv(4096)
                room_name_size, op, state = int.from_bytes(data[:1], "big"), int.from_bytes(data[1:2], "big"), int.from_bytes(data[2:3], "big")
                payload_size = int.from_bytes(data[3:self.HEADER_MAX_BYTE], "big")
                body = data[self.HEADER_MAX_BYTE:]
                room_name, payload = body[:room_name_size].decode("utf-8"), body[room_name_size:room_name_size + payload_size].decode("utf-8")
                token = secrets.token_bytes(self.TOKEN_MAX_BYTE)

                if op == 1:  # 新しいルーム作成
                    conn.send(token)
                    self.room_members_map[room_name] = [token]
                    print(f"新しいルーム: {room_name} (Host: {payload})")
                elif op == 2:  # 既存ルームに参加
                    conn.send(str(self.room_members_map.keys()).encode("utf-8"))
                    room_name = conn.recv(4096).decode("utf-8")
                    self.room_members_map[room_name].append(token)
                    conn.send(token)
                    print(f"{payload}が既存ルーム {room_name} に参加")
                
                self.clients_map[token] = [client_addr, room_name, payload, 1 if op == 1 else 0, None]
                print(self.clients_map)

            except Exception as e:
                print(f'Error: {e}')
            finally:
                conn.close()

    def start(self):
        self.tcp_main()

class UDPServer:
    def __init__(self, address, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((address, port))
        self.room_members_map, self.clients_map = TCPServer.room_members_map, TCPServer.clients_map

    def handle_message(self):
        while True:
            data, client_addr = self.sock.recvfrom(4096)
            room_name_size, token_size = int.from_bytes(data[:1], "big"), int.from_bytes(data[1:2], "big")
            body = data[2:]
            room_name, token = body[:room_name_size].decode("utf-8"), body[room_name_size:room_name_size + token_size]

            if self.clients_map[token][0] != client_addr:
                self.clients_map[token][0] = client_addr  # クライアントアドレスを更新
                print(f"{self.clients_map[token][2]}がルーム {room_name} に参加")
            else:
                self.clients_map[token][-1] = time.time()
                message = f"{self.clients_map[token][2]}: {body[room_name_size + token_size:].decode('utf-8')}"
                print(f"Room: {room_name}, {message}")
                self.relay_message(room_name, message)

    def relay_message(self, room_name, message):
        for member_token in self.room_members_map[room_name]:
            self.sock.sendto(message.encode(), self.clients_map[member_token][0])  # 全員にメッセージ送信

    def send_time_tracking(self):
        while True:
            time.sleep(60)  # 1分ごとに追跡
            for token, info in list(self.clients_map.items()):
                if time.time() - info[-1] > 300:  # 5分間通信がないクライアントを削除
                    room, user = info[1], info[2]
                    if info[3] == 1:  # ホスト退出
                        self.relay_message(room, f"ホスト {user} が退出しました")
                        del self.room_members_map[room]
                    else:
                        self.room_members_map[room].remove(token)
                    del self.clients_map[token]

    def start(self):
        threading.Thread(target=self.handle_message).start()
        threading.Thread(target=self.send_time_tracking).start()

if __name__ == "__main__":
    tcp_server = TCPServer('0.0.0.0', 9001)
    udp_server = UDPServer('0.0.0.0', 9002)
    threading.Thread(target=tcp_server.start).start()
    threading.Thread(target=udp_server.start).start()
