# Capitulo 9 

Nesse capítulo serão exploradas técnicas de exfiltração que podem ser úteis para o nosso estudo

## Explorando a técnica de exfiltração

[Exfiltração ou sequestro de dados](https://en.wikipedia.org/wiki/Data_theft) é um termo para indicar o roubo de arquivos de dados criptografados de um sistema invadido. Usaremos para a exfiltração 3 métodos principais: por email, por transferência de arquivos e por postagens web. 

Vale ressaltar que, para máquinas Windows, usaremos o PyWin32, uma série de libs próprias para manipulação de dados no Windows que usamos no capítulo 8. Usaremos automação do COM (Component Object Model), que oferece serviços de integração legais para o nosso uso.

### Criptografando e descriptografando arquivos

Utilizaremos a lib `pycryptodomex` para realizar as tarefas de criptografia:

```bash
pip install pycryptodomex
```

Em `cryptor.py`:

```py
from Cryptodome.Cipher import AES, PKCS1_OAEP
from Cryptodome.PublicKey import RSA
from Cryptodome.Random import get_random_bytes
from io import BytesIO

import base64
import zlib
```

Inicialmente, a nossa ideia é fazer uma criptografia híbrida, combinando partes de *criptografia simétrica* (que usa uma mesma chave tanto para encriptar quando para decriptar) e partes de *criptografia assimétrica* (que usa o esquema de chave pública e privada). O AES é um exemplo do primeiro caso, ele lida com grandes quantidades de texto. Utilizaremos ele para cifrar informações que queremos exfiltrar.

Para a criptografia assimétrica usaremos o RSA, usando um par de chaves. Utilizaremos ele para encriptar/decriptar a **chave** do AES, pois ele é mais eficiente em textos pequenos.

Essa abordagem híbrida é muito comum no TLS (Transport Layer Security, já visto em capítulos anteriores). Começaremos o código com uma função para criar o par de chaves do RSA:

```py
def generate(): # Função para gerar o par de chaves
    new_key = RSA.generate(2048)    # Usa a lib do RSA para gerar uma chave de 2048 bits
    private_key = new_key.export_key()  # pega a chave privada
    public_key = new_key.publickey().export_key()   # pega a chave pública
    
    with open('key.pri', 'wb') as f:
        f.write(private_key)    # salva em arquivos
        
    with open('key.pub', 'wb') as f:
        f.write(public_key)     
```

Agora, com as chaves em mãos, criaremos uma função para auxiliar a leitura das chaves:

```py
def get_rsa_cipher(keytype):   # passamos o tipo de chave
    with open(f'key.{keytype}') as f:
        key = f.read()      # lemos a chave
    rsa_key = RSA.import_key(key)   # importamos como chave RSA 
    return (PKCS1_OAEP.new(rsa_key), rsa_key.size_in_bytes())   # retornamos o objeto Cipher da chave (PKCS) e o seu tamanho em bytes
```

Com as chaves geradas e com os objetos de chave capturados, vamos criar uma função de encriptar os dados:

```py
def encrypt(plaintext):
    # Comprime o texto simples usando o algoritmo de compressão zlib.
    # Isso reduz o tamanho dos dados antes da criptografia, o que pode
    # melhorar a eficiência do armazenamento ou transmissão.
    compressed_text = zlib.compress(plaintext)
    
    # Gera uma chave de sessão aleatória de 16 bytes.
    # Essa chave será usada para criptografia simétrica (AES).
    session_key = get_random_bytes(16)
    
    # Cria uma instância do cifrador AES no modo EAX, que é um modo seguro
    # e inclui autenticação para garantir a integridade dos dados.
    cipher_aes = AES.new(session_key, AES.MODE_EAX)
    
    # Encripta o texto comprimido usando a chave de sessão e calcula
    # um "tag" de autenticação que será usado para verificar a integridade
    # e autenticidade do texto cifrado.
    cipher_text, tag = cipher_aes.encrypt_and_digest(compressed_text)
    
    # Obtém uma instância de um cifrador RSA usando uma chave pública
    cipher_rsa, _ = get_rsa_cipher('pub')
    
    # Encripta a chave de sessão AES com o RSA. Isso permite que a chave de sessão
    # seja compartilhada com segurança, já que apenas o destinatário com a chave
    # privada correspondente poderá decifrá-la.
    encrypted_session_key = cipher_rsa.encrypt(session_key)
    
    # Concatena a chave de sessão cifrada (RSA), o "nonce" gerado pelo AES,
    # o "tag" de autenticação e o texto cifrado. Esse é o payload completo
    # que será necessário para decifrar a mensagem.
    # nonce = number used once, é uma forma de verificar que o algoritmo está funcionando
    # pois verifica se o mesmo texto cifrado, com a mesma chave, não produzam a mesma mensagem
    # se parece com um salt
    msg_payload = encrypted_session_key + cipher_aes.nonce + tag + cipher_text
    
    # Codifica o payload final em base64 para garantir que ele possa ser
    # armazenado ou transmitido de forma segura, sem problemas de codificação.
    encrypted = base64.encodebytes(msg_payload)
    
    # Retorna o payload criptografado codificado em base64.
    return encrypted
```

Finalmente, faremos então a função para decriptar o texto:

```py
def decrypt(encrypted):
    # Cria um buffer de memória para a mensagem encriptada, facilita a leitura (usada no .read() em sequencia)
    encrypted_bytes = BytesIO(base64.decodebytes(encrypted))
    cipher_rsa, keysize_in_bytes = get_rsa_cipher('pri')    # pega a chave privada e o tamanho dela em bytes (será usado para 
                                                            # capturar os bytes da chave AES)
    
    # Sabemos que no encrypt() a sequencia era : chave + nonce + tag + texto. Sabemos também que o nonce e a tag ambos tem 16 bytes
    # Como estamos com um buffer do BytesIO, a cada leitura "sobra" o resto da mensagem, possibilitando esse sequenciamento de leitura
    encrypted_session_key = encrypted_bytes.read(keysize_in_bytes)  # pega os N bytes da chave encriptada
    nonce = encrypted_bytes.read(16)    # sabemos que ambos são de 16 bytes pois é o tamanho padrão para o modo EAX
    tag = encrypted_bytes.read(16)
    ciphertext = encrypted_bytes.read() # finalmente, lemos a mensagem
    
    session_key = cipher_rsa.decrypt(encrypted_session_key) # decriptamos a chave
    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)  # Criamos um objeto AES com o texto usando o nonce e a chave
    decrypted = cipher_aes.decrypt_and_verify(ciphertext, tag)  # verificamos e decriptamos, resultando no arquivo original comprimido
    
    plaintext = zlib.decompress(decrypted)
    return plaintext    # descomprimimos e retornamos


if __name__ == '__main__':
    # Usamos primeiro o generate para pegar as chaves. No caso real pode ser que se queira deixá-las em lugares separados

    # generate()
    
    plaintext = b'TESTE '
    print(decrypt(encrypt(plaintext)))  # testamos a função com um texto binário
```

Pronto! Agora você tem seu próprio método de encriptar e decriptar mensagens de forma segura.