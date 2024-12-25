import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading

class NetCat:
    def __init__ (self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    def run(self):
        if self.args.listen:
            self.listen()
        else:
            self.send()

    def send(self):
        self.socket.connect((self.args.target, self.args.port))
        if self.buffer:
            self.socket.send(self.buffer)
        
        try:
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    data = self.socket.recv(5)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 5:
                        break
                
                if response:
                    print(response)
                    buffer = input('> ')
                    buffer += '\n'
                    self.socket.send(buffer.encode())

        except KeyboardInterrupt:
            print("Interrompido pelo usuário")
            self.socket.close()
            sys.exit()

    def listen (self):
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(
                target=self.handle, args=(client_socket,)
            )
            client_thread.start()

    def handle(self, client_socket):
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())
        
        if self.args.upload:
            file_buffer = b''
            while True:
                data = client_socket.recv(20)
                file_buffer += data
                if len(data) < 20:
                    break
                
            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)
            message = f'Upload salvo em {self.args.upload}'
            client_socket.send(message.encode())

        if self.args.command:
            cmd_buffer = b''
            while True:
                try:
                    client_socket.send(b'cmd: #> ')
                    while '\n' not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    response = execute(cmd_buffer.decode())
                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b''

                except Exception as e:
                    print(f'Servidor encerrado: {e}')
                    self.socket.close()
                    sys.exit()


def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return 
    
    output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
    return output.decode()




if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Netcat Python',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''Exemplo: 
            netcat.py -t 192.168.1.108 -p 5555 -l -c                    # shell de comando
            netcat.py -t 192.168.1.108 -p 5555 -l -u=mytext.txt         # upload de arquivo
            netcat.py -t 192.168.1.108 -p 5555 -e= \"cat /etc/passwd\"   # executar comando
            echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135            # enviar texto para a porta 135
                                                             
            netcat.py -t 192.168.1.108 -p 5555                          # conectar ao servidor            
        '''))
    parser.add_argument('-c', '--command', action='store_true', help='shell de comando')
    parser.add_argument('-e', '--execute', help='executar comando especificado')
    parser.add_argument('-l', '--listen', action='store_true', help='ouvir')
    parser.add_argument('-p', '--port', type=int, default=5555, help='porta especificada')
    parser.add_argument('-t', '--target', default='127.0.0.1', help='IP alvo')
    parser.add_argument('-u', '--upload', help='receber upload de arquivo')

    args = parser.parse_args()
   
    if args.listen:
        buffer = ''
    else:
        buffer = sys.stdin.read()
    
    nc = NetCat(args, buffer.encode()) 
    nc.run()
