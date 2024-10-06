import socket
import threading

# メッセージを受信する関数
def recv_msg(sock):
    while True:
        try:
            msg = sock.recv(1024).decode('utf-8')
            if msg: print(f"\n{msg}")
        except: 
            print("接続が切れました。")
            sock.close()
            break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 12345))  # サーバに接続

    threading.Thread(target=recv_msg, args=(sock,), daemon=True).start()  # 受信スレッド開始

    print("接続しました。メッセージを入力してください（'exit'で終了）:")
    while True:
        msg = input()
        if msg.lower() == 'exit': break
        sock.send(msg.encode('utf-8'))  # メッセージ送信

    sock.close()

if __name__ == "__main__":
    main()
