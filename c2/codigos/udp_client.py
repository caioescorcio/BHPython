import socket

target_host = "127.0.0.1"
target_port = 9997

# Cria-se um objeto socket
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Envia-se os dados
client.sendto(b"TESTE", (target_host,target_port))

# Recebe alguns dados
data, addr = client.recvfrom(4096)

print(data.decode())
print(addr)
client.close()
