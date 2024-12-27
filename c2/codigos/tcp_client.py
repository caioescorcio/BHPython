import socket

target_host = "127.0.0.1"
target_port = 9998

# Cria-se um objeto socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Conexão
client.connect((target_host,target_port))

# Envio de dados
client.send(b"TESTE")

# Recebimento de dados
response = client.recv(4096)

print(response.decode())
client.close()