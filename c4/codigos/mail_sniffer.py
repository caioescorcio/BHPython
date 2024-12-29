from scapy.all import sniff, TCP, IP

def packet_callback(packet):
    if packet[TCP].payload:
        mypacket = str(packet[TCP].payload)
        if 'user' in mypacket.lower() or 'pass' in mypacket.lower():
            print(f'[*] Destino: {packet[IP].dst}')
            print(f'[*] {mypacket}')
    
def main():
    sniff(filter='tcp port 80',
          prn=packet_callback, store=0)

if __name__ == '__main__':
    main()

