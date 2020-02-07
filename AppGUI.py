import socket
import json
import tkinter as tk
import tkinter.messagebox
from tkinter import ttk
import tkinter.scrolledtext as tkst
import time
import threading
server_ip=""
server_port=""
server_alias=""
connections = [] #alias ip port message
newone = []
lock = threading.Lock()
def DCfunc(app):
    global  server_alias,server_port,server_ip
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((server_ip, int(server_port)))
        s.send('DC'.encode('utf-8'))
        s.send(json.dumps({'alias': server_alias}).encode('utf-8'))
        s.send("EOF".encode('utf-8'))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((server_ip, int(server_port)))
        s.send('DC'.encode('utf-8'))
        s.send(json.dumps({'alias': server_alias}).encode('utf-8'))
        s.send("EOF".encode('utf-8'))
        s.close()
        app.destroy()
    except:
        app.destroy()


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

class SampleApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self._frame = None
        self.switch_frame(StartPage)

    def switch_frame(self, frame_class):
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.pack()


class StartPage(tk.Frame):
    def connect(self,ip, port, alias):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((ip, port))
        except Exception as e:
            print(e)
            return False, e
        s.send('CN'.encode('utf-8'))
        login_detail = json.dumps({'alias': alias, 'password': '1234'})
        s.send(login_detail.encode('utf-8'))
        s.close()
        return True, None

    def __init__(self, master):
        tk.Frame.__init__(self, master)
        global server_alias, server_ip, server_port
        cav = tk.Canvas(self, height=0, width=200).pack()

        label_ip = tk.Label(self, text="Server IP:").pack()
        edittext_ip = tk.Entry(self, bd=5)
        edittext_ip.pack()

        label_port = tk.Label(self, text="Port:").pack()
        edittext_port = tk.Entry(self, bd=5)
        edittext_port.pack()

        label_alias = tk.Label(self, text="Alias:").pack()
        edittext_alias = tk.Entry(self, bd=5)
        edittext_alias.pack()

        btnConnect = tk.Button(self, bg="white", activebackground="gray", text="Connect", bd=2, command=lambda:self.btnConnect_click(edittext_alias.get(),edittext_port.get(),edittext_ip.get(),master)).pack()
        #cav.pack()

    def btnConnect_click(self,alias,port,ip,master):
        global server_alias, server_port, server_ip
        server_alias = alias
        server_port = int(port)
        server_ip = ip
        login, sideload = self.connect(ip, int(port), alias)
        if login == False:
            tk.messagebox.showinfo("", sideload)
        else:
            master.switch_frame(PageTwo)

class PageTwo(tk.Frame):
    lst = []
    def check_online(self,ip, port, alias):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((ip, int(port)))
        s.send('OL'.encode('utf-8'))
        s.send(json.dumps({'alias': alias}).encode('utf-8'))
        s.send("EOF".encode('utf-8'))
        #online_list = get_data(s)
        return_data = ""
        char = s.recv(10000)
        online_list=json.loads(char.decode())
        s.close()
        return online_list


    def process_chat(self,target, lst,tab_parent):
        if target[-6:] == "online":
            target=target[:-7]
        else:
            return
        for i in tab_parent.tabs():
            if tab_parent.tab(i, option="text") == target: return
        lock.acquire()
        global connections
        for alias in lst:
            if target == alias['alias']:
                connections.append({'alias': alias['alias'], 'ip': alias['ip'], 'port': alias['port'], 'messages': []})
        lock.release()
        #them tab
        self.addtab(target,tab_parent)

    def update_lstbox(self, lstbox):
        global server_ip, server_port, server_alias
        self.lst = self.check_online(server_ip, int(server_port), server_alias)
        lstbox.delete(0, 'end')
        for alias in self.lst:
            lstbox.insert('end', alias['alias']+'-'+alias['status'])
        lstbox.pack()
        self.after(7000, self.update_lstbox, lstbox)

    def btnSent_click(self,text,entry,mess):
        if text=="": return
        global server_alias,server_ip,server_port
        entry.delete(0,tk.END)
        mess.insert('insert',server_alias+": "+text +"\n")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((server_ip, 12500))
        s.send("MS".encode('utf-8'))
        send_data = {'alias': server_alias, 'content': text}
        s.send(json.dumps(send_data).encode('utf-8'))
        s.send("eof".encode('utf-8'))
        return

    def btnClose_click(self,tabname):
        tabname.destroy()

    def addtab(self,alias,tab_parent):
        tabname = ttk.Frame(tab_parent)
        mess = tkst.ScrolledText(tabname, wrap='word', width=25, height=10, bg='beige')
        mess.pack(fill='x')
        edittext_message = tk.Entry(tabname, bd=5)
        edittext_message.pack(side='bottom',fill='x')
        btnClose = tk.Button(tabname, text="CLOSE", command=lambda: self.btnClose_click(tabname))
        btnClose.pack(side='left')
        btnSent = tk.Button(tabname, text="SENT",command= lambda:self.btnSent_click(edittext_message.get(),edittext_message,mess))
        btnSent.pack(side='right')

        tab_parent.add(tabname, text=alias)

    def update_msg(self, old_connections):
        global connections, newone
        lock.acquire()
        if connections != old_connections:
            old_connections = connections
            for msg in newone:
                print(msg['alias'] + " said " + msg['content'])
                #add tab here
            newmsg=[]
            lock.release()
        else:
            lock.release()
        self.after(200, self.update_msg, old_connections)

    def __init__(self, master):
        super(PageTwo, self).__init__()
        global connections
        self.update_msg([])
        global server_alias, server_ip, server_port
        tk.Frame.__init__(self, master)
        cav = tk.Canvas(self, height=0, width=200).pack(fill='both')
        tab_parent = ttk.Notebook(self)
        maintab= ttk.Frame(tab_parent)
        tab1= ttk.Frame(tab_parent)

        tab_parent.add(maintab, text="Online")

        #widgets for a main tab
        lstbox = tk.Listbox(maintab)
        self.update_lstbox(lstbox)
        lstboxoff= tk.Listbox(maintab)
        tab_parent.pack(expand=1, fill='both')
        btnChat = tk.Button(maintab, text="CHAT",
                        command=lambda: self.process_chat(lstbox.get(lstbox.curselection()), self.lst, tab_parent))

        btnChat.pack()



def gui_serve():
    app = SampleApp()
    app.protocol("WM_DELETE_WINDOW", lambda: DCfunc(app))
    app.mainloop()

def listener_serve():
    global connections
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 8600))
    s.listen(5)
    while True:
        c, addr = s.accept()
        threading.Thread(target=service_process, args=(c, addr)).start()


def service_process(c,addr):
    global connections, newone
    command = c.recv(2).decode()
    if command == "MS":
        new_message = get_data(c)
        lock.acquire()
        for connection in connections:
            if connection['alias'] == new_message['alias']:
                newone.append(new_message)
                connection['messages'].append(new_message['content'])
                lock.release()
                return
        newone.append(new_message)
        connections.append(
                    {'alias': new_message['alias'], 'ip': addr[0], 'port': 12500, 'messages': [new_message['content']]})
        lock.release()
        return


if __name__ == "__main__":
    threading.Thread(target=gui_serve).start()
    threading.Thread(target=listener_serve).start()
