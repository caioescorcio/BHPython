# Capitulo 2 

## Ferramentas básicas de rede

Nesse capítulo, o autor explora ferramentas comuns de rede, mas feitas em Python. A inspiração é: você invadiu uma empresa, mas na máquina que você está não tem nenhuma ferramenta de rede (Netcat, Wireshark, etc), mas tem Python.

Nesse capítulo usaremos a lib `socket` do Python. A sua documentação está [aqui](https://docs.python.org/3/library/socket.html).

### Um breve resumo sobre redes Python

Nessa parte, o autor contextualiza sobre o protocolo [TCP](https://pt.wikipedia.org/wiki/Protocolo_de_Controle_de_Transmiss%C3%A3o) (Transmission Control Protocol) e sobre o protocolo [UDP](https://pt.wikipedia.org/wiki/Protocolo_de_datagrama_do_usu%C3%A1rio) (User Datagram Protocol).

O primeiro passo é criar alguns clientes e servidores simples.

### Cliente TCP

Vamos criar um cliente TCP, ou seja, um código de comunicação entre o cliente e algum servidor por TCP:

```py
import socket

target_host = "www.google.com"
target_port = 80

# Cria-se um objeto socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conexão
client.connect((target_host,target_port))

# Envio de dados
client.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

# Recebimento de dados
response = client.recv(4096)

print(response.decode())
client.close()
```

A explicação do código, em complemento aos comentários é:

Na instanciação da classe `socket`:
- `AF_INET`, é uma constante que indica que o endereço/hostname IPv4 padrão (AF = Address Family). Caso fosse IPv6, usaríamos `AF_INET6`
- `SOCK_STREAM`, é uma constante que indica que iremos nos comunicar com TCP. Sua variante poderia ser `SOCK_DGRAM`, que indicaria uma conexão UDP.

- `(target_host,target_port)` estão concatenados pois é a tupla que forma o objeto `_Addr`

- `client.send(b"GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")`, o `b"` antes da string de mensagem indica que iremos mandar a mensagem em como *bytes*.

- `response = client.recv(4096)`, indica que receberemos uma mensagem de "4096" caracteres. É o tamanho do buffer desejado.


Esse é um cliente básico de TCP. Ele assume que a conexão com o host está aberta para enviar as mensagens, que ele está esperando que nós enviemos as mensagens primeiro e que o servidor sempre nos retornará dados de maneira oportuna. Ao passar do livro teremos mais técnicas mais avançadas para complementar esse cliente.

### Cliente UDP

Seguindo a lógica do cliente acima, o código para o cliente UDP é:

```py
import socket

target_host = "127.0.0.1"
target_port = 9997

# Cria-se um objeto socket
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Envia-se os dados
client.sendto(b"AAABBBCCC", (target_host,target_port))

# Recebe alguns dados
data, addr = client.recvfrom(4096)

print(data.decode())
print(addr)
client.close()
```

Note que a conexão não é linkada como no TCP, pois a conexão UDP não espera um host sempre ligado. Logo, ao invés de um client via `connect`, é usado um `sendto`, com a mensagem e o host. Mesma lógica para o `recvfrom`:

![UDPCLIENT](../imagens/c2-udp.png)

Note que, para ver o código funcionando, é necessário que o Host esteja preparado para receber a mensagem na porta indicada. Para isso foi usado um `netcat` (`nc -ulp 9997` com as flags `-u` para conexão UDP, `-l` para *listen* e `-p 9997` para a porta), Ao apertar `enter` na conexão UDP, após o recebimento da mensagem, foi possível receber no terminal de execução do Python a mensagem "enter" como resposta e printar o host.


### Servidor TCP

Agora com esses fundamentos de conexões, criaremos um servidor TCP. Isto é, código que, quando rodado, mexa com conexões TCP:

```py
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
```

As explicações estão ao longo do código. Usamos o código TCP anterior para testá-lo (`tcp_client.py`), usando como `target_host` 127.0.0.1 e `target_port` 9998. Ao executar `tcp_client.py` com a mensagem "TESTE", recebemos no terminal de `tcp_server.py`:

```bash
[*] Conexão aceita de: 127.0.0.1:56050
[*] Recebido: TESTE
```

E, no terminal de `tcp_client.py`:

```bash
ACK
```

O próximo passo, agora com ferramentas de conexão em mãos, é criar um [Proxy](https://en.wikipedia.org/wiki/Proxy_server)!

### Substituindo o Netcat

Agora começaremos o desenvolvimento do netcat, uma ferramenta quase que universal e indispensável no contexto de Redes para segurança. Primeiramente vamos criar uma forma de executar comandos no terminal quando recebemos-os no Python:

```py
# Imports gerais, não são todos usados nesse código
import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading

# Função execute
def execute(cmd):
    # Divide o input em várias subdivisões
    cmd = cmd.strip()
    if not cmd:
        return 

    # subprocess.check_output executa um shell como se fosse no terminal. 
    # stderr=subprocess.STDOUT indica que as mensagens de erro devem vir no próprio output
    output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
    return output.decode()

if __name__ == '__main__':
    print(execute("ls"))
```

Vale ressaltar que, do jeito que está, o código funciona apenas no Linux devido a como o Windows trata comandos `shell`. Uma adaptação poderia ser:

```py
import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading



def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return 

    # Verifica o OS
    if sys.platform.startswith('win'):
        output = subprocess.check_output(shlex.split(cmd), 
                                        stderr=subprocess.STDOUT,
                                        shell=True)     # Aceita comandos Shell
        # Faz o decode com base no que vem do Windows
        return output.decode('cp1252')
    
    # Roda normal
    output = subprocess.check_output(shlex.split(cmd), 
                                    stderr=subprocess.STDOUT,
                                    )
    return output.decode()

if __name__ == '__main__':
    print(execute("dir"))
```

Em sequência, modificamos a `__main__` para servir como "guia" do netcat. Para isso será usada a `lib` ArgumentParser, que serve para fazer a interpretação dos argumentos quando o código é chamado.:

```py
if __name__ == '__main__':
    # Instanciação do parser
    parser = argparse.ArgumentParser(
        # Nome
        description='Netcat Python',
        # Tipo = Help
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # Epílogo (final do --help) com um exemplo
        epilog=textwrap.dedent('''Exemplo: 
            netcat.py -t 192.168.1.108 -p 5555 -l -c                    # shell de comando
            netcat.py -t 192.168.1.108 -p 5555 -l -u=mytext.txt         # upload de arquivo
            netcat.py -t 192.168.1.108 -p 5555 -e= \"cat /etc/passwd\"   # executar comando
            echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135            # enviar texto para a porta 135
                                                             
            netcat.py -t 192.168.1.108 -p 5555                          # conectar ao servidor            
        '''))

    # Argumentos que podem ser passados

    # action='store_true' significa que o valor é um booleano e que, por padrão, é False
    parser.add_argument('-c', '--command', action='store_true', help='shell de comando')
    parser.add_argument('-e', '--execute', help='executar comando especificado')
    parser.add_argument('-l', '--listen', action='store_true', help='ouvir')
    # Define tipos e valor padrão
    parser.add_argument('-p', '--port', type=int, default=5555, help='porta especificada')
    parser.add_argument('-t', '--target', default='192.168.1.203', help='IP alvo')
    parser.add_argument('-u', '--upload', help='fazer upload de arquivo')

    # args é um array que armazena os argumentos usado
    args = parser.parse_args()
    if args.listen:
        buffer = ''
    else:
        buffer = sys.stdin.read() # buffer é o que está no input
    
    # Usa os argumentos e o buffer para instancia o uso da classe NetCat
    nc = NetCat(args, buffer.encode()) 
    nc.run()
```

Sobre a classe NetCat, temos a seguinte estrutura inicial:

```py
class NetCat:
    def __init__ (self, args, buffer=None):
        # Instancia os argumentos, buffer e cria o socket
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # socket.setsockopt é um modificador de opções do socket
        # no caso, estamos mudando a opção SOL_SOCKET (opções no nível do socket)
        # colocamos o parametro REUSEADDR para 1, isso implica que o socket pode ser
        # reaberto imediatamente após ser fechado, mesmo caso ele esteja em "estado de espera"
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Função principal
    def run(self):
        # caso se queira escutar, executa a função listen()
        if self.args.listen:
            self.listen()
        else:
        # caso contrário, executa a função send()
            self.send()
```
