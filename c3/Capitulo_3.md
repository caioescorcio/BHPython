# Capitulo 3 

Neste capítulo, o autor trata da criação de um *sniffer* de rede, que nada mais é que um rastreador de pacotes. Ele intercepta e mostra as informações de rede que são passadas pela máquina alvo e, por isso, é uma tecnologia muito útil no contexto de segurança. 

Existem sniffers já consolidados, como o Wireshark ou o Scapy, do python. Contudo é importante saber fazer o próprio sniffer a fim de entender como funciona a Rede.

## Desenvolvendo um sniffer
 
Nesse trecho ele introduz um pouco sobre o que é um sniffer

### Criando uma ferramenta de descobertas de hosts UDP

O autor introduz a ideia de descoberta de hosts. Quando é enviado um datagrama UDP para uma porta fechada de um host, ele envia de volta uma mensagem ICMP (Internet Control Message Protocol - que informa que o host está ativo). Então é essencial que usemos uma porta UDP que provavelmente não será utilizada ou sondar várias portas.

É possível adicionar mais portas e lógica para varreduras de portas de hosts descobertos ao estilo NMAP.

### Sniffing de Padotes no Windows e no Linux

Como o processo para acessar sockets brutos no Windows é diferente do do Linux, primeiro é necessário determinar em qual plataforma o host-alvo está operando. No windows, é necessário implatar algumas flags adicionais para controles de input/output (IOCTL - input/output control) que habilita o modo promíscuo de rede. Primeiramente, configuramoso sniffer para lermos um único pacote:

```py
import socket
import os

# Instancia o host desejado
HOST = '192.168.100.77'

def main():
    # Verifica se o sistema da execução é Windows
    if os.name == 'nt':
        # No Windows não é necessário filtrar as mensagens do tipo ICMP, pois é possível receber todos os tipos
        socket_protocol = socket.IPPROTO_IP
    else:
        # No Linux é necessário especificar que procuramos ICMP
        socket_protocol = socket.IPPROTO_ICMP
    
    # Início do socket, com a opção de mensagem ao final, esperando pacotes brutos
    sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
    # Bind (UDP)
    sniffer.bind((HOST,0))
    # Configuração para receber o IP origem na mensagem
    sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    
    if os.name == 'nt':
        # Passo adicional de config do IOCTL para modo promiscuo
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
        
    # Printa a primeira mensagem recebida
    print(sniffer.recvfrom(65565))
    
    if os.name == 'nt':
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)

if __name__ == '__main__':
    main()    
```

### Explorando o código

É necessário exectuar em modo administrador para que seja bem sucedido o código, seja no Windows seja no Linux.

Após a execução, é de se esperar uma mensagem assim:

`(b'E\x00\x00(g\x07@\x00j\x06\xc4k\rY\xb3\x0e\xc0\xa8dM\x01\xbb\xdc\xddh\x8d\xe9-\xb7\xa0\x88BP\x10@\x02\x1a>\x00\x00', ('13.89.179.14', 0))`

Com algum host de origem mandando algo para a máquina.

### Decodificando o protocolo IP

Com a captura de mensagem feita, podemos começar a filtrar informações que nos seriam úteis. Contudo é fato que, dada a naturez binária da comunicação de máquinas, é necessário que façamos um estudo sobre o protocolo IP para que entendamos a mensagem:

![IP](../imagens/ip_header.png)

Em cada octeto do protocolo IP, temos uma estrurua pré-determinada de informações. Isso será útil para que possamos filtrá-las.

Para isso, podemos usar o módulo `ctypes`, que permite a utilização de tipos de dados em Python como se fosse na linguagem C. Também é possível usar o módulo `struct`, que realiza realiza a conversão entre Python e C tratando os dados como objeto. Ambos os métodos serão mostrados e funcionam igualmente bem.

#### Módulo ctypes

Criaremos um código para ler um pacote IP e analisar os seus campos de forma separada:

```py
from ctypes import *
import socket
import struct

# Instanciação da classe IP como um tipo de Structure (que vem do ctypes)
class IP(Structure):
    # Divisão dos campos da struct criada para o ctypes
    _fields_ = [
        ("version",         c_ubyte,    4),  	# Unsigned char de 4 bits
        ("ihl",             c_ubyte,    4),  	# Unsigned char de 4 bits
        ("tos",             c_ubyte,    8),  	# char de 1 byte (8 bits)
        ("len",             c_ushort,  16),  	# Unsigned short de 2 bytes
        ("id",              c_ushort,  16),  	# Unsigned short de 2 bytes
        ("offset",          c_ushort,  16),  	# Unsigned short de 2 bytes
        ("ttl",             c_ubyte,    8),  	# char de 1 byte
        ("protocol_num",    c_ubyte,    8),  	# char de 1 byte
        ("sum",             c_ushort,  16),  	# Unsigned short de 2 bytes
        ("src",             c_uint32,  32),  	# Unsigned int de 4 bytes
        ("dst",             c_uint32,  32)  	# Unsigned int de 4 bytes
    ]
    
    # cls é a referencia à classe para o ctypes e coloca os dados recebidos na structure
    def __new__ (cls, socket_buffer=None):
        return cls.from_buffer_copy(socket_buffer)
    
    # No init, são convertidos os IPs de destino e de origem, vindos da struct alinhados para a esquerda
    def __init__ (self, socket_buffer=None):
        # Endereco de IP legivel por humanos
        self.src_address = socket.inet_ntoa(struct.pack("<L", self.src))
        self.dst_address = socket.inet_ntoa(struct.pack("<L", self.dst))
```

#### Módulo struct

Em relação ao módulo struct, o código ficaria assim:

```py
import ipaddress
import struct

# Instanciação da classe
class IP:
    def __init__(self, buff=None):
        # Ordem os bytes dos dados, como no kali x64 é little endian, usamos o '<'
        # Byte = B, Hexa = H, 4s = int 32 bits
        header = struct.unpack('<BBHHHBBH4s4s', buff)

        # Para dividir o primeiro byte (8 bits), fazemos o shift de 4 bits para encontrar a versão
        self.ver = header[0] >> 4
        # Fazemos um filtro para os primeiros 4 bits para encontrar o ihl
        self.ihl = header[0] & 0xF
        
        # Capuramos dado a dado tomando como referencia a divisão feita
        self.tos = header[1]
        self.len = header[2]
        self.id = header[3]
        self.offset = header[4]
        self.ttl = header[5]
        self.protocol_num = header[6]
        self.sum = header[7]
        self.src = header[8]
        self.dst = header[9]
        
        # Enderecos de IP legiveis por humanos
        self.src_address = ipaddress.ip_address(self.src)
        self.dst_address = ipaddress.ip_address(self.dst)
        
        # Mapear constantes de protocolo com seus nomes
        self.protocol_map = {1: "ICMP", 6: "TCP", 17: "UDP"}
```

Para os próximos passos usaremos de base o código de `IP_struct.py`

### Desenvolvendo o decodificador de IP

Agora implementaremos o sniffer com o método de decode (`sniffer_ip_header_decode.py`), juntando as partes feitas até então:

```py
import ipaddress
import struct
import os
import socket
import sys

# Classe IP feita anteriormente
class IP:
    def __init__(self, buff=None):
        header = struct.unpack('<BBHHHBBH4s4s', buff)
        self.ver = header[0] >> 4
        self.ihl = header[0] & 0xF
        
        self.tos = header[1]
        self.len = header[2]
        self.id = header[3]
        self.offset = header[4]
        self.ttl = header[5]
        self.protocol_num = header[6]
        self.sum = header[7]
        self.src = header[8]
        self.dst = header[9]
        
        self.src_address = ipaddress.ip_address(self.src)
        self.dst_address = ipaddress.ip_address(self.dst)

        self.protocol_map = {1: "ICMP", 6: "TCP", 17: "UDP"}
        
        # Discriminação do protocolo
        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except Exception as e:
            print("%s Sem protocolo para %s" % (e, self.protocol_num))
            self.protocol = str(self.protocol_num)
            
def sniff(host):
    # Sniffer feito anteriormente
    if os.name == 'nt':
        socket_protocol = socket.IPPROTO_IP
    else:
        socket_protocol = socket.IPPROTO_ICMP
        
    sniffer = socket.socket(socket.AF_INET, 
                            socket.SOCK_RAW, socket_protocol)
    
    sniffer.bind((host,0))
    sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    
    if os.name == 'nt':
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
        
    # loop
    try:
        while True:
            raw_buffer = sniffer.recvfrom(65535)[0]
            # Decode do IP
            ip_header = IP(raw_buffer[0:20])
            # Print do que está acontecendo
            print("Protocolo: %s %s -> %s" % (ip_header.protocol, 
                                                ip_header.src_address,
                                                ip_header.dst_address))

    # Crtl+C para encerrar
    except KeyboardInterrupt:
        if os.name == 'nt':
            sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
        sys.exit()
                

if __name__ == '__main__':
    # Espera o argumento para o host
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = '192.168.100.77'  
        
    sniff(host)
```

Pronto! Agora temos uma forma de descobrimento de hosts usando o sniffer. Faremos então uma forma de decodificar as mensagens ICMP para averiguar as informações passadas por ela.

### Decodificando o ICMP

Usando o mesmo método para o decode de IP, vejamos o seguinte gráfico:

![ICMP](../imagens/icmp.png)

Observe que ele apresenta 64 bits no total que nos importa (2 primeiras linhas). O resto da mensagem (abaixo) é sequencia da mensagem inteira do pacote, vinda do protocolo IP

Procuramos apenas as mensagens com `Type == 3`, que caracterizam `Destination Unreachable`, e com `Code == 3`, que caracterizam `Port Unreachable`, pois são os tipos de mensagens UDP que estamos gerando. Modificando o nosso sniffer, acrescentamos uma nova classe `ICMP`:

```py
[...]

class ICMP:
    def __init__(self, buff):
        header = struct.unpack('<BBHHH', buff)
        self.type = header[0]
        self.code = header[1]
        self.sum = header[2]
        self.id = header[3]
        self.seq = header[4]

def sniff...

... 

    try:
        while True:
            raw_buffer = sniffer.recvfrom(65535)[0]
            ip_header = IP(raw_buffer[0:20])
            # Se for ICMP, tratamos
            if ip_header.protocol == 'ICMP':
                print("Protocolo: %s %s -> %s" % (ip_header.protocol, 
                                                    ip_header.src_address,
                                                    ip_header.dst_address))
                # Print da versão e do cabeçalho
                print(f'Versão: {ip_header.ver}')
                print(f'Comprimento do cabeçalho: {ip_header.ihl} TTL: {ip_header.ttl}')
                
                # O cáculo do offset é o comprimento do IHL (Internet Header Lenght, de palavras de 32 bits)
                # Multiplicado por 4, pois são 4 bytes por palavra
                offset = ip_header.ihl * 4 # Basicamente acha onde o Protocolo IP acaba dentro do pacote
                # Extrai os 8 bytes seguintes, que são representativos do ICMP
                buff = raw_buffer[offset:offset + 8]
                # Instancia o ICMP e printa seu tipo e código
                icmp_header = ICMP(buff)
                print('ICMP -> Tipo: %s Código: %s\n' % (icmp_header.type, 
                                                         icmp_header.code))
```

Pronto! Agora temos um indentificador de mensagens ICMP, que será útil para o descobrimento de hosts da rede em sequência!

Complementando o código, criaremos o `scanner.py`, que faz o que nos era proposto inicialmente: mandar pacotes UDP para hosts em portas inutilizadas e esperar o ICMP para encontrar os hosts ativos:

```py
import ipaddress
import struct
import os
import socket
import threading
import time
import sys

# Especificar a sua sub-rede, para verificarmos todos os hosts disponíveis
SUBNET = '192.168.100.0/24'
# String qualquer para enviar no UDP
MESSAGE = 'ALGUEM'

# Classes como as anteriores
class IP:
    def __init__(self, buff=None):
        header = struct.unpack('<BBHHHBBH4s4s', buff)
        self.ver = header[0] >> 4
        self.ihl = header[0] & 0xF
        
        self.tos = header[1]
        self.len = header[2]
        self.id = header[3]
        self.offset = header[4]
        self.ttl = header[5]
        self.protocol_num = header[6]
        self.sum = header[7]
        self.src = header[8]
        self.dst = header[9]
        
        self.src_address = ipaddress.ip_address(self.src)
        self.dst_address = ipaddress.ip_address(self.dst)

        self.protocol_map = {1: "ICMP", 6: "TCP", 17: "UDP"}
        
        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except Exception as e:
            print("%s Sem protocolo para %s" % (e, self.protocol_num))
            self.protocol = str(self.protocol_num)

class ICMP:
    def __init__(self, buff):
        header = struct.unpack('<BBHHH', buff)
        self.type = header[0]
        self.code = header[1]
        self.sum = header[2]
        self.id = header[3]
        self.seq = header[4]
        

# Método de mandar mensagens UDP, para esperar os ICMP
def udp_sender():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
        # Procura os IP para envio da menssagem (em bytes) na lista de hosts para essa subnet
        for ip in ipaddress.ip_network(SUBNET).hosts(): 
            sender.sendto(bytes(MESSAGE, 'utf8'), (str(ip), 65212)) # mensagem UDP para (host, porta inutilizada)
          
# Nosso scanner
class Scanner:  
    
    def __init__(self, host):
        # Instanciação para inicio do envio das mensagens
        self.host = host
        if os.name == 'nt':
            socket_protocol = socket.IPPROTO_IP
        else:
            socket_protocol = socket.IPPROTO_ICMP
            
        self.socket = socket.socket(socket.AF_INET, 
                                socket.SOCK_RAW, socket_protocol)
        
        self.socket.bind((host,0))
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        
        if os.name == 'nt':
            self.socket.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)
            
    # Função de sniffing
    def sniff(self):
        hosts_up = set([f'{str(self.host)} *'])
        
        try:
            while True:
                raw_buffer = self.socket.recvfrom(65535)[0]
                ip_header = IP(raw_buffer[0:20])
                
                # Procura mensagens ICMP, do mesmo jeito anterior
                if ip_header.protocol == 'ICMP':                   
                    offset = ip_header.ihl * 4
                    buff = raw_buffer[offset:offset + 8]
                    icmp_header = ICMP(buff)
                    
                    # Filtra as que vieram do nosso envio UDP
                    if icmp_header.code == 3 and icmp_header.type == 3:
                        # Verifica se o endereço da mensagem está na nossa sub-rede
                        if ipaddress.ip_address(ip_header.src_address) in ipaddress.IPv4Network(SUBNET):
                            # Verifica se, na mensagem de retorno contém a mensagem original: (string de tamanho b, string[a:] 
                            # verifica os últimos b-a bits da string) pois, pelo protocolo, ela deveria ser o último apendice 
                            # de uma UDP mal sucedida
                            if raw_buffer[len(raw_buffer) - len(MESSAGE) :] == bytes(MESSAGE, 'utf8'):
                                # Acha o host
                                tgt = str(ip_header.src_address)
                                if tgt != self.host and tgt not in hosts_up:
                                    # Adiciona à lista de hosts
                                    hosts_up.add(str(ip_header.src_address))
                                    print(f'Host ativo: {tgt}')

        except KeyboardInterrupt:
            if os.name == 'nt':
                self.socket.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
            print("Interrompido pelo usuário")
            # Printa a lista de hosts
            if hosts_up:
                print(f'Resumo: Hosts ativos em {SUBNET}:')
                for host in sorted(hosts_up):
                    print(f'{host}')
            else:
                print("Nenhum host encontrado.")
            print('')
            sys.exit()
                    

if __name__ == '__main__':
    if len(sys.argv) == 2:
        host = sys.argv[1]
    else:
        host = '192.168.100.77'  
        
    s = Scanner(host)
    # Espera 5 s depois da criação do scanner, para dar tempo ao setup dos sockets
    time.sleep(5)
    # Inicia a thread de mandar mensagens UDP
    t = threading.Thread(target=udp_sender)
    t.start()
    # Procura os hosts
    s.sniff()
    
```

Vale ressaltar que a lib `ipaddress` facilitou o trabalho de criação da lista de hosts da subnet!

Pronto! Agora temos scanner de rede para verificarmos os hosts ativos!

### Explorando o código

Tudo funcionou!