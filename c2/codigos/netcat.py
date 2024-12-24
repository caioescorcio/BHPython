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
    parser.add_argument('-t', '--target', default='192.168.1.203', help='IP alvo')
    parser.add_argument('-u', '--upload', help='fazer upload de arquivo')

    args = parser.parse_args()
    if args.listen:
        buffer = ''
    else:
        buffer = sys.stdin.read()
    
    nc = NetCat(args, buffer.encode()) 
    nc.run()
