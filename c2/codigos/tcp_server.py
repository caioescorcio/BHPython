import socket
import threading

# Definição do endereço em que queremos que a porta execute
IP = '0.0.0.0'      # o IP 0.0.0.0 indica que todas as interfaces de rede locais na determinada porta vêm para o server
PORT = 9998

def main():
    # Início do server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # O bind coloca a dada porta para uso
    server.bind((IP,PORT))
    # Número máximo de conexões deve ser 5
    server.listen(5)
    print(f'[*] Ouvindo em {IP}:{PORT}')

    while True:
        # Aceita a conexão. "client" instancia um client no código para comunicar com o "address" de onde vem a conexão
        client, address = server.accept() 
        print(f'[*] Conexão aceita de: {address[0]}:{address[1]}')
        # Inicia uma thread para fazer a comunicação
        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()

def handle_client(client_socket):
    with client_socket as sock:
        # Recebe as mensagens e manda o ACK ("acknowledgement")
        request = sock.recv(1024)
        print(f'[*] Recebido: {request.decode("utf-8")}')
        sock.send(b'ACK')

if __name__ == '__main__':
    main()
