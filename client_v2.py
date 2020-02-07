import socket
import json


def get_data(s):
    return_data = ""
    char = s.recv(1)
    while True:
        return_data += char.decode()  # Decode from UTF-8
        char = s.recv(1)  # Receive char by char
        try:
            json.loads(return_data)  # Success to do json.loads <=> end of Alias
            break
        except Exception as e:
            continue
    return json.loads(return_data)


def connect(ip, port, alias):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((ip, port))
    except Exception as e:
        print(e)
        return False, e
    s.send('CN'.encode('utf-8'))
    login_detail = json.dumps({'alias': alias})
    s.send(login_detail.encode('utf-8'))
    s.close()
    return True, s


def check_online(ip, port, alias):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((ip, port))
    s.send('OL'.encode('utf-8'))
    online_list = get_data(s)
    return online_list


import threading


def service(c, addr):
    global connections
    command = c.recv(2).decode()
    if command == "MS":
        message = get_data(c)
        for connection in connections:
            if connection['alias'] == message['alias']:
                connection['message'].append(message['content'])
                break
        # ADD NEW TAB OR TAB EXISTS THEN CHANGE TITLE TAB
        c.close()
        return
    if command == "DC":
        alias = get_data(c)
        for connection in connections:
            if connection['alias'] == alias['alias']:
                connections.delete(connection)
        c.close()
        return
        # DELETE TAB


def send_message(ip,port,alias,message):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((ip, port))
    s.send("MS".encode('utf-8'))
    send_data = {'alias': alias, 'content': message}
    s.send(json.dumps(send_data).encode('utf-8'))
    s.send("eof".encode('utf-8'))
    s.close()
    return


def listener():
    listen_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_s.bind(("", 8500))
    listen_s.listen(5)
    while True:
        c, addr = listen_s.accept()
        threading.Thread(target=service, args=(c, addr)).start()
