import socket
import json
import sys
import threading
import time
from pathlib import Path
import base64
import re
import os

# Connect: CN
# Disconnect: DC
# Message: MS
# Update: UP
# ONLINE: OL
# FILE: FI
# ACQUIRE: AC

lock = threading.Lock()
message = []
latest_index = 0
port = 17191
pattern='^/acquire ...'

def update(ip, port, alias):
    global latest_index
    while True:
        update_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        update_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        update_s.connect((ip, port))
        update_s.send('UP'.encode('utf-8'))
        lock.acquire()
        update_param = {'alias': alias, 'latest_index': latest_index}
        lock.release()
        update_param = json.dumps(update_param)
        update_s.send(update_param.encode('utf-8'))
        update_s.send("eof".encode('utf-8'))
        update_data = ""
        command = update_s.recv(2)
        if command.decode() == "NO":
            continue
        elif command.decode() == "UP":
            while True:
                char = update_s.recv(1)
                update_data += char.decode()  # Decode from UTF-8
                try:
                    json.loads(update_data)  # Success to do json.loads <=> end of Alias
                    update_s.recv(3)  # flush the socket
                    break
                except:
                    continue
            update_data = json.loads(update_data)

            if latest_index != int(update_data['latest_index']):
                lock.acquire()
                latest_index = int(update_data['latest_index'])
                lock.release()
                for message in update_data['messages']:
                    print(message[1] + ": " + message[2])
        update_s.close()
        time.sleep(1.2)


IP = input('Enter server to connect: ')
alias = input('Enter your alias: ')

# Initial connect to register as participant
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Procedure
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

s.connect((IP, port))
jsonalias = json.dumps({'alias': alias})  # Alias aka nick name. JSON is dictionary type
s.send('CN'.encode('utf-8'))  # Command to be sent
s.send(jsonalias.encode('utf-8'))
s.send('eof'.encode('utf-8'))
char = s.recv(1)
messages = ""
while True:
    messages += char.decode()  # Decode from UTF-8
    char = s.recv(1)  # Receive char by char
    try:
        json.loads(messages)  # Success to do json.loads <=> end of Alias
        s.recv(3)  # flush the socket
        break
    except:
        continue
messages = json.loads(messages)
for message in messages['messages']:
    print(message[1] + ": " + message[2])
lock.acquire()
latest_index = int(messages['latest_index'])
lock.release()
s.close()
threading.Thread(target=update, args=(IP, port, alias)).start()
while True:  # Message sending here
    message = input('Enter your message: ')
    if message == '/stop':
        s.close()
        sys.exit(0)

    elif message == '/online':
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((IP, port))
        s.send('OL'.encode('utf-8'))
        userlist = ""
        char = s.recv(1)
        while True:
            userlist += char.decode()  # Decode from UTF-8
            char = s.recv(1)  # Receive char by char
            try:
                json.loads(userlist)  # Success to do json.loads <=> end of Index
                s.recv(3)  # flush the socket
                break
            except Exception as e:
                continue
        userlist = json.loads(userlist)
        print(userlist)
        s.close()

    elif message == '/file':
        path = input("Enter file path: ")
        path = Path(path)
        try:
            f = open(str(path), 'rb')
            file = base64.b64encode(f.read()).decode('utf-8')
            send_file = {'alias': alias, 'name': path.name, 'file': file}
            f.close()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((IP, port))
            s.send("FI".encode('utf-8'))
            s.send(json.dumps(send_file).encode('utf-8'))
            s.send("eof".encode('utf-8'))
        except Exception as e:
            print(e)
        index = ""
        char = s.recv(1)
        while True:
            index += char.decode()  # Decode from UTF-8
            char = s.recv(1)  # Receive char by char
            try:
                json.loads(index)  # Success to do json.loads <=> end of Index
                s.recv(3)  # flush the socket
                break
            except Exception as e:
                continue
        lock.acquire()
        latest_index = int(json.loads(index)['latest_index'])
        lock.release()
        s.close()

    elif re.match(pattern, message):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((IP, port))
        s.send('AC'.encode('utf-8'))
        request = {'name': message[9:]}
        s.send(json.dumps(request).encode('utf-8'))
        s.send("eof".encode('utf-8'))
        file = ""
        while True:
            char = s.recv(1)  # Receive char by char
            file += char.decode()  # Decode from UTF-8
            try:
                json.loads(file)  # Success to do json.loads <=> end of Index
                s.recv(3)  # flush the socket
                break
            except Exception as e:
                continue
        path = ""
        file = json.loads(file)['file'].encode('utf-8')
        try:
            path = str(Path(os.getcwd() + "/download"))
            os.mkdir(path)
        except WindowsError as e:
            if e.errno == 183:
                pass
        filedata = base64.b64decode(file)
        try:
            f = open(str(path) + '/' + message[9:], 'wb')
            f.write(filedata)
            f.close()
        except Exception as e:
            print(e)
        print("File is saved at: " + str(path))
        s.close()

    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((IP, port))
        message = {'alias': alias, 'content': message}
        jsonmessage = json.dumps(message)
        s.send('MS'.encode('utf-8'))
        s.send(jsonmessage.encode('utf-8'))
        s.send('eof'.encode('utf-8'))
        index = ""
        char = s.recv(1)
        while True:
            index += char.decode()  # Decode from UTF-8
            char = s.recv(1)  # Receive char by char
            try:
                json.loads(index)  # Success to do json.loads <=> end of Index
                s.recv(3)  # flush the socket
                break
            except Exception as e:
                continue
        lock.acquire()
        latest_index = int(json.loads(index)['latest_index'])
        lock.release()
        s.close()
