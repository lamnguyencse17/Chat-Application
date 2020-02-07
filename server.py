import socket
import json
import threading
import base64
import os
from pathlib import Path

try:
    os.mkdir(str(Path(os.getcwd() + "/file")))
except WindowsError as e:
    if e.errno == 183:
        pass

lock = threading.Lock()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 17191

s.bind(('', port))

s.listen(5)
message_index = -1
information = {'participant': [], 'message': []}
filelog = []
filevault = str(Path(os.getcwd() + "/file"))

def check_participant(addr):
    for participant in information['participant']:
        if str(addr) == participant[0]:
            return False
    return True

def service(c, addr):
    global message_index, information, filelog, filevault
    command = c.recv(2).decode()  # Listen for command
    while True:
        if command == "CN":
            if check_participant(addr):  # Check the list if participant exists
                alias = ""
                char = c.recv(1)
                while True:
                    alias += char.decode()  # Decode from UTF-8
                    char = c.recv(1)  # Receive char by char
                    try:
                        json.loads(alias)  # Success to do json.loads <=> end of Alias
                        c.recv(3)  # flush the socket
                        break
                    except:
                        continue
                alias = json.loads(alias)
                lock.acquire()
                information['participant'].append((addr, alias['alias']))  # Add to Server Log
                lock.release()
                update_message = information['message'][-5:]  # Get last 5 messages to send as update
                update_message = {'latest_index': message_index, 'messages': update_message}
                c.send(json.dumps(update_message).encode('utf-8'))
                c.send('eof'.encode('utf-8'))
                c.close()
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
            index = {}
            lock.acquire()
            message_index += 1
            index = json.dumps({"latest_index": str(message_index), })
            lock.release()
            c.send(index.encode('utf-8'))
            c.send("eof".encode('utf-8'))
            lock.acquire()
            information['message'].append((message_index, message['alias'], message['content']))
            lock.release()
            c.close()
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
            messages = information['message'][(index - int(param['latest_index'])):]
            lock.release()
            diff = []
            for message in messages:
                if message[1] != param['alias']:
                    diff.append(message)
            if diff:
                c.send("UP".encode('utf-8'))
                send_data = {'latest_index': index, 'messages': diff}
                c.send(json.dumps(send_data).encode('utf-8'))
                c.send("eof".encode('utf-8'))
            else:
                c.send("NO".encode('utf-8'))
            c.close()
            return
        elif command == "OL":
            lock.acquire()
            participants = json.dumps(information['participant'])
            lock.release()
            c.send(participants.encode('utf-8'))
            c.send("eof".encode('utf-8'))
            c.close()
            return
        elif command == "FI":
            file = ""
            while True:
                char = c.recv(1)  # Receive char by char
                file += char.decode()  # Decode from UTF-8
                try:
                    json.loads(file)  # Success to do json.loads <=> end of Index
                    c.recv(3)  # flush the socket
                    break
                except Exception as e:
                    continue
            lock.acquire()
            message_index += 1
            index = json.dumps({"latest_index": str(message_index), })
            lock.release()
            c.send(index.encode('utf-8'))
            c.send("eof".encode('utf-8'))
            file = json.loads(file)
            content = file['alias'] + " has sent a file " + file['name']
            lock.acquire()
            index = message_index
            information['message'].append((message_index, file['alias'], content))
            lock.release()
            filedata = base64.b64decode(file['file'].encode('utf-8'))
            try:
                path = str(filevault + '/' + file['name'])
                f = open(path, "wb")
                f.write(filedata)
                f.close()
            except Exception as e:
                print(e)
            lock.acquire()
            filelog.append(({'index': index, 'name': file['name'], 'path': str(filevault + '/' + file['name'])}))
            lock.release()
            return

        elif command == "AC":
            name = ""
            while True:
                char = c.recv(1)  # Receive char by char
                name += char.decode()  # Decode from UTF-8
                try:
                    json.loads(name)  # Success to do json.loads <=> end of Index
                    c.recv(3)  # flush the socket
                    break
                except Exception as e:
                    continue

            name = json.loads(name)['name']
            target = ""
            for file in filelog:
                if file['name'] == name:
                    target = file
                    break
            print(target)
            path = target['path']
            f = open(path, 'rb')
            file = base64.b64encode(f.read()).decode('utf-8')
            send_file = {'file': file}
            f.close()
            c.send(json.dumps(send_file).encode('utf-8'))
            s.send("eof".encode('utf-8'))
            s.close()
            return




while True:
    c, addr = s.accept()
    threading.Thread(target=service, args=(c, addr)).start()  # Each thread processes a client

