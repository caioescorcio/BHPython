import socket
import sys
import threading

HEX_FILTER = ''.join([chr(i) if len(repr(chr(i))) == 3 else '.' for i in range(256)])

def hexdump(src, length=16, show=True):
    if isinstance(src,bytes):
        src = src.decode()

    results = list()

    for i in range(0, len(src), length):
        word = str(src[i:i+length])

        printable = word.translate(HEX_FILTER)
        hexa = ' '.join([f'{ord(c):02X}' for c in word])
        hexwidth = length*3
        results.append(f'{i:04x}    {hexa:<{hexwidth}}  {printable}')
    
    if show:
        for line in results:
            print(line)
    else:
        return results
    

def recieve_from(connection):
    buffer = b""
    connection.settimeout(5)

    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data

    except Exception as e:
        pass

    return buffer


def request_handler(buffer):
    return buffer
def response_handler(buffer):
    return buffer


def proxy_handler(client_socket, 
                  remote_host, remote_port,
                  recieve_first):
    
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host,remote_port))

    if recieve_first:
        remote_buffer = recieve_from(remote_socket)
        hexdump(remote_buffer)
    
        remote_buffer = response_handler(remote_buffer)

        if len(remote_buffer):
            print("[<==] Enviando %d bytes para o localhost" % len(remote_buffer))
            client_socket.send(remote_buffer)

    while True:
        local_buffer = recieve_from(client_socket)
        if len(local_buffer):
            line = "[==>] Recebidos %d bytes do localhost" % len(local_buffer)
            print(line)
            hexdump(local_buffer)
        
        remote_buffer = recieve_from(remote_socket)

        if len(remote_buffer):
            print("[<==] Enviando %d bytes para o localhost" % len(remote_buffer))
            hexdump(remote_buffer)

            remote_buffer = response_handler(remote_buffer)
            client_socket.send(remote_buffer)
            print("[<==] Enviado para o localhost")

        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] Não há mais dados. Fechando conexões")
            break


def server_loop(local_host, local_port,
                remote_host, remote_port,
                recieve_first):
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        server.bind((local_host,local_port))
    except Exception as e:
        print("Problema ao conectar: %r" % e)
        print("[!!] Falha ao ouvir em %s:%d" % (local_host,local_port))
        print("[!!] Verifique outros sockets de escuta ou corrija as permissões")
        sys.exit(0)
    
    print("[*] Ouvindo em %s:%d" % (local_host,local_port))
    server.listen(5)
    while True:
        client_socket, addr = server.accept()
        line = "> Conexão de entrada recebida de %s:%d" % (addr[0],addr[1])
        print(line)

        proxy_thread = threading.Thread(
            target=proxy_handler,
                   args=(client_socket, remote_host, remote_port, recieve_first)
                    )
        proxy_thread.start()

        
def main():
    if len(sys.argv[1:]) != 5:
        print("Uso: ./proxy.py [localhost] [localport]", end='')
        print(" [remotehost] [remoteport] [recieve_first]")
        print("Exemplo: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")

    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    recieve_first = sys.argv[5]

    if 'True' in recieve_first:
        recieve_first = True
    else:
        recieve_first = False

    server_loop(local_host, local_port, remote_host, remote_port, recieve_first)

    
 

if __name__ == '__main__':
    main()