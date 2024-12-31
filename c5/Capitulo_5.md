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