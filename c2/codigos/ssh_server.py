import paramiko
import os
import socket
import sys
import threading

CWD = os.path.dirname(os.path.realpath(__file__))
HOSTKEY = paramiko.RSAKey(filename=os.path.join(CWD, 'chave.key'))

class Server (paramiko.ServerInterface):
    def __init__ (self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
    def check_auth_password (self, username, password):
        if (username == 'caio') and (password == 'caio'):
            return paramiko.AUTH_SUCCESSFUL
            
if __name__ == '__main__':
    server = '192.168.100.3'
    ssh_port = 2222
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((server, ssh_port))
        
        sock.listen(100)
        print("[+] Ouvindo conexões...")
        client, addr = sock.accept()
    except Exception as e:
        print("[-] Falha na escuta:" + str(e))
        sys.exit(1)
    else:
        print('[+] Conexão estabelecida!', client, addr)
        
    session = paramiko.Transport(client)
    session.add_server_key(HOSTKEY)
    server = Server()
    session.start_server(server=server)
    
    chan = session.accept(20)
    if chan is None:
        print('*** Sem canal.')
        sys.exit(1)
        
    print("[+] Autenticado!")
    print(chan.recv(1024))
    chan.send('Bem vindo ao SSH')
    try:
        while True:
            command = input('Insira o comando: ')
            if command != 'exit':
                chan.send(command)
                r = chan.recv(8192)
                print(r.decode())
            else:
                chan.send('exit')
                print('exiting')
                session.close()
                break
    except KeyboardInterrupt:
        session.close()