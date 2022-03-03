from urllib import response
from websocket_server import WebsocketServer
import tempfile
import os
import shutil
import subprocess
import json

prefix = "firejail --noroot --private --quiet --cpu=1 --nonewprivs --nogroups --nice=19 --hostname=host --net=none --no3d --nosound --x11=none --rlimit-cpu=1 -- stdbuf -o 0 "

class Project:
    def __init__(self):
        self.dir = tempfile.mkdtemp()

    def __del__(self):
        self.destroy()

    def run(self, cmd):
        output = subprocess.run(prefix + cmd, cwd=self.dir, capture_output=True, text=True, shell=True)

        if len(output.stderr) > 0:
            return {"ok": False, "response": output.stderr}
        else:
            return {"ok": True, "response": output.stdout}
        

    def destroy(self):
        try:
            shutil.rmtree(self.dir)
        except:
            print("destroy")

    def addFiles(self, files: dict[str, str]):
        for filename, content in files.items():
            filepath = os.path.join(self.dir, filename)

            if not os.path.isdir(os.path.dirname(filepath)):
                os.makedirs(os.path.dirname(filepath))

            file = open(filepath, "w")
            file.write(content + "\n")
            file.close



# Called for every client connecting (after handshake)
def new_client(client, server):
    print("New client connected and was given id %d" % client['id'])
    server.send_message_to_all("Hey all, a new client has joined us")
    client["project"] = Project()

# Called for every client disconnecting
def client_left(client, server):
    print("Client(%d) disconnected" % client['id'])
    client["project"].destroy()


# Called when a client sends a message
def message_received(client, server, message):
    message = json.loads(message)

    print("Client(%d)" % (client['id']), message["data"])
    
    client["project"].addFiles(message["data"])

    result = client["project"].run(message["cmd"])
    print(result)
    server.send_message(client, json.dumps(result))
    

PORT=10000
server = WebsocketServer(port = PORT)
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
server.set_fn_message_received(message_received)
server.run_forever()