import socket
import json
import threading
import time
import sqlite3
import os
from pathlib import Path

message_index = -1
DEFAULT_PATH = 'db.sqlite3'
participants = [] # ip port alias
messages = [] # index alias content
try:
    os.mkdir(str(Path(os.getcwd() + "/file")))
except WindowsError as e:
    if e.errno == 183:
        pass
filelog = []
filevault = str(Path(os.getcwd() + "/file"))
lock = threading.Lock()


def db_connect(db_path=DEFAULT_PATH):
    con = sqlite3.connect(db_path)
    return con


def get_data(c):
    return_data = ""
    char = c.recv(1)
    while True:
        return_data += char.decode()  # Decode from UTF-8
        char = c.recv(1)  # Receive char by char
        try:
            json.loads(return_data)  # Success to do json.loads <=> end of Alias
            break
        except Exception as e:
            continue
    return json.loads(return_data)


def check_login_detail(login_detail, c):
    global messages
    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT * from users")
    users = cur.fetchall()

    for user in users:
        if user[1] == login_detail['alias']:
            if user[2] == login_detail['password']:
                c.sendall("OK".encode("utf-8"))
                lock.acquire()
                update_message = messages[-5:]
                update_message = {'latest_index': message_index, 'messages': update_message}
                c.sendall(json.dumps(update_message).encode('utf-8'))
                c.sendall("EOF".encode('utf-8'))
                lock.release()
                con.close()
                return True
            else:
                c.sendall("WR".encode("utf-8"))
                con.close()
                return False
    cur.execute("INSERT INTO users (alias, password) VALUES (?, ?)", (login_detail['alias'], login_detail['password']))
    con.commit()
    con.close()
    c.sendall("RE".encode("utf-8"))
    return True


def connection_service(c, addr):
    global participants, messages, filelog, filevault, message_index
    command = c.recv(2).decode()
    if command == "CN":
        login_detail = get_data(c)
        if check_login_detail(login_detail, c):
            lock.acquire()
            for participant in participants:
                if participant['alias'] == login_detail['alias']:
                    participant['ip'] = addr[0]
                    participant['port'] = addr[1]
                    participant['alias'] = login_detail['alias']
                    participant['status'] = 'online'
                    lock.release()
                    return
            participants.append({'ip': addr[0], 'port': addr[1], 'alias': login_detail['alias'], 'status': 'online'})
            lock.release()
        else:
            return
        return
    elif command == "OL":
        alias = get_data(c)
        print(alias)
        c.recv(3)
        lock.acquire()
        local_participants = participants
        lock.release()
        return_value = []
        for participant in local_participants:
            if participant['alias'] != alias['alias']:
                return_value.append(participant)
        c.sendall(json.dumps(return_value).encode('utf-8'))
        c.sendall("EOF".encode('utf-8'))
        #c.close()
        return
    elif command == "MS":
        message = ""
        while True:
            char = c.recv(1)
            message += char.decode()
            try:
                json.loads(message)  # Success to do json.loads <=> end of Message
                c.recv(3)  # flush the socket
                break
            except:
                continue
        message = json.loads(message)
        #print(message)
        index = {}
        lock.acquire()
        message_index += 1
        index = json.dumps({"latest_index": str(message_index), })
        lock.release()
        c.sendall(index.encode('utf-8'))
        c.sendall("eof".encode('utf-8'))
        lock.acquire()
        messages.append({'index': message_index, 'alias': message['alias'], 'content': message['content']})
        lock.release()
        return
    elif command == "UP":
        param = ""
        while True:
            char = c.recv(1)
            param += char.decode()
            try:
                json.loads(param)  # Success to do json.loads <=> end of Message
                c.recv(3)  # flush the socket
                break
            except:
                continue
        param = json.loads(param)
        lock.acquire()
        index = message_index
        tempmessages = messages[(int(param['latest_index']) - index):]
        lock.release()
        diff = []
        for message in tempmessages:
            if message['alias'] != param['alias']:
                diff.append(message)
        if diff:
            c.sendall("UP".encode('utf-8'))
            send_data = {'latest_index': index, 'messages': diff}
            c.sendall(json.dumps(send_data).encode('utf-8'))
            c.sendall("eof".encode('utf-8'))
        else:
            c.sendall("NO".encode('utf-8'))
        c.close()
        return
    elif command == "DC":
        dc_detail = get_data(c)
        lock.acquire()
        for participant in participants:
            if dc_detail['alias'] == participant['alias']:
                participant['status'] = 'offline'
                break
        lock.release()
        return


def keep_alive():
    global participants, lock
    while True:
        if len(participants) != 0:
            for participant in participants:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(3)
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.connect((participant['ip'], 12500))
                    participant['status'] = 'online'
                except socket.timeout as e:
                    print(str(participant['alias'] + ' ' + str(e)))
                    lock.acquire()
                    participant['status'] = 'offline'
                    lock.release()
                    print(participants)
        time.sleep(3)



def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = input("Enter port to bind: ")
    s.bind(('', int(port)))
    s.listen(20)
    threading.Thread(target=keep_alive).start()
    while True:
        c, addr = s.accept()
        threading.Thread(target=connection_service, args=(c, addr)).start()


if not Path('db.sqlite3').exists():
    con = db_connect()
    cur = con.cursor()
    creation = """CREATE TABLE users (
    id integer PRIMARY KEY,
    alias text NOT NULL,
    password text NOT NULL)"""
    cur.execute(creation)
    con.close()

if __name__ == '__main__':
    main()
