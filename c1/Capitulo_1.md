# Capitulo 1 

## Configurando o seu ambiente Python 

Inicialmente, o autor apresenta uma ideia de máquina virtual do Kali Linux (distro voltada para segurança) e introduz ideias de como configurar sua máquina para estudar o livro.

### Instalando o Kali Linux

Bem direto ao ponto, o autor introduz a instalação do Kali com VM e a sua atualização:

```bash
sudo apt update
apt list --upgradable
sudo apt upgrade
sudo apt dist-upgrade
sudo apt autoremove
```

Como já possuia o Kali instalado, apenas rodei o `bash` para atualizá-lo. 

O autor instrui a usarmos o Kali em VM para programar usando o Python, mas, por comodidade, usarei o Windows nativo no meu computador, pois já o tenho instalado.

### Configurando o Python 3

Para a configuração do ambiente, os autores recomendam o uso de um ambiente virtual (`venv`), para a separação de cada uma das funcionalidade usadas. Será usado o VSCode como IDE e um terminal `cmd` (não `powershell`) para a execução de comandos

Para a sua criação no Windows, com o [Python3](https://www.python.org/downloads/) instalado e o [`pip`](https://packaging.python.org/en/latest/tutorials/installing-packages/) atualizado, cria-se um diretório arbitrário para a execução do ambiente virtual (que chamamos de venv3):

```cmd
~ mkdir codigos
~ python -m venv venv3
~ .\venv3\Scripts\activate.bat
```

Isso executará o ambiente virtual do Python no terminal. O significado de `python -m venv venv3` é: "Python, no pacode `venv` (`-m venv`) execute como `venv3`. 

Para sair do ambiente usamos:

```cmd
(venv3) ..\ deactivate
```

O autor compara o gerenciador de pacotes do Pythom (`pip`) com o gerenciador de pacotes do Linux (`apt`) e exemplifica o uso do pip para instalar uma biblioteca de `web scrapping` no ambiente virtual (que será usada apenas no capítulo 5):

```cmd
(venv3) ..\ pip install lxml
```

E, para atestar que foi corretamente instalada:

```cmd
(venv3) ..\ python
>>> from lxml import etree
>>> exit()
```

Como o Python é uma linguagem interpretada, é possível executar comando nele dinamicamente, como o que acontece no código acima. Nele, o comando `python` é chamado e, com a interface de código (`>>> `), são executados comandos. O primeiro comando (`from lxml import etree`) tenta fazer um `import` da biblioteca instalda agora há pouco e, logo em seguida, sai do programa. Se houvesse um erro na instalação, o terminal do Python quebraria.

Na pasta-mãe do repositório tem um `.bat` que cria no diretório atual um venv. Ele será usado para o início de cada capítulo:

```bat
@echo off
:: Cria a pasta 'codigos'
mkdir codigos

:: Navega para a pasta criada
cd codigos

:: Cria um ambiente virtual Python chamado 'venv3'
python -m venv venv3

:: Ativa o ambiente virtual
call venv3\Scripts\activate.bat

:: Exibe uma mensagem informando que o ambiente foi ativado
echo Ambiente virtual 'venv3' ativado!
```

### Instalando um IDE

Nessa parte o autor ensina a instalar uma IDE, uso o [VS Code](https://code.visualstudio.com/download) e continuarei com ele. 

### Boas práticas de código limpo

Nesse trecho, o autor nos instrui a construir boas práticas para a linguagem Python. Ele sugere como o guia do Python Enhancement Proposals (PEP) [número 8](https://peps.python.org/pep-0008/) (guia de estilo). Um resumo dos pontos principais, mas não seguidos à risca, encontra-se a seguir:

#### Identação:

Em funções:

```py
# Correto:

# Alinhado com o delimitador
foo = long_function_name(var_one, var_two,
                         var_three, var_four)

# Adicione 4 espaços extras para diferenciar um argumento dos demais
def long_function_name(
        var_one, var_two, var_three,
        var_four):
    print(var_one)

# Delimite os argumentos com diferença da variável atribuida
foo = long_function_name(
    var_one, var_two,
    var_three, var_four)
```

Em condicionais:

```py
# Sem identação extra
if (this_is_one_thing and
    that_is_another_thing):
    do_something()

# Adicione um comentário que vá ser distinguido em diferentes editores
# "usar highlight de sintaxe"
if (this_is_one_thing and
    that_is_another_thing):
    # "já que acontece tal tal tal podemos tal"
    do_something()

# Adicione identação extra na linha de continuação condicional 
if (this_is_one_thing
        and that_is_another_thing):
    do_something()
```

Em arrays de várias linhas:

```py
# Feche os colchetes alinhado com o inicio da linha
my_list = [
    1, 2, 3,
    4, 5, 6,
    ]
result = some_function_that_takes_arguments(
    'a', 'b', 'c',
    'd', 'e', 'f',
    )
```

Ou:

```py
# Feche os colchetes alinhado com o inicio da declaração
my_list = [
    1, 2, 3,
    4, 5, 6,
]
result = some_function_that_takes_arguments(
    'a', 'b', 'c',
    'd', 'e', 'f',
)
```

#### Tamanho máximo de linha

Cada linha deve ter no máximo 79 caracteres. Para colocá-la no VS Code, aperte `Ctrl+Shift+P` e digite `settings`. Altere as opções do usuário (`.json`) adicionando um campo escrito `"editor.rulers": [79]`, isso criará uma "régua" para o seu VS Code.

É possível usar `\` para separar linhas no Python:

```py
s = "exemplo exemplo exemplo exemplo exemplo exemplo exemplo exemplo exemplo exemplo exemplo exemplo exemplo exemplo "

# É igual a 

s = "exemplo exemplo exemplo exemplo exemplo exemplo exemplo exemplo exemplo \
    exemplo exemplo exemplo exemplo exemplo "
```

#### Operadores

```py
# Correto
# Operadores ao início dos operandos
income = (gross_wages
          + taxable_interest
          + (dividends - qualified_dividends)
          - ira_deduction
          - student_loan_interest)
```

#### Linhas em branco

Cerque as `definições de classe` e `função de nível` superior com *duas linhas* em branco.

As `definições de método` dentro de uma classe são cercadas por uma *única linha* em branco.

Use linhas em branco em funções, com moderação, para indicar seções lógicas.

#### Imports

Divida os `import`'s:

```py
# Correto:
import os
import sys
from subprocess import Popen, PIPE

# É mais claro para o leitor uma divisão mais precisa do que vai ser usado
import mypkg.sibling
from mypkg import sibling
from mypkg.sibling import example

# Ambos estão certos
from myclass import MyClass
from foo.bar.yourclass import YourClass
```

#### Espaços em branco

Em resumo, nao use espaços em branco entre variáveis e `[]`, `()`, etc. Use o bom senso com os espaços

```py
# Correto:
spam(ham[1], {eggs: 2})
foo = (0,)
if x == 4: print(x, y); x, y = y, x

# Correto:
i = i + 1
submitted += 1
x = x*2 - 1
hypot2 = x*x + y*y
c = (a+b) * (a-b)

def munge(input: AnyStr): ...
def munge() -> PosInt: ...

# ------------------------------------------------------------

# Errado:
spam( ham[ 1 ], { eggs: 2 } )
bar = (0, )
if x == 4 : print(x , y) ; x , y = y , x

# Errado:
i=i+1
submitted +=1
x = x * 2 - 1
hypot2 = x * x + y * y
c = (a + b) * (a - b)

def munge(input:AnyStr): ...
def munge()->PosInt: ...
```

#### Virgulas de continuidade

```py
# Correto:
FILES = ('setup.cfg',)

FILES = [
    'setup.cfg',
    'tox.ini',
    ]
initialize(FILES,
           error=True,
           )

# ------------------------------------------------------------


# Errado:
FILES = 'setup.cfg',

FILES = ['setup.cfg', 'tox.ini',]
initialize(FILES, error=True,)
```

#### Comentários

Sempre dê um espaço após o `#` : `# Comentário`.

Não comente o óbvio, pois polui o código. Comente o que achar útil e com a funcionalidade. Evite comentários na própria linha, caso sejam inúteis.


#### Nomes de variáveis:

Use o bom senso, não use 'l', 'I' ou 'O' sós, pois são confundidos `1` e `0`. Convenções

- Pacotes e módulos: `pequenos`, evita-se `_`
- Classes: `CapWords`
- Variáveis: `cUrtOs`, suas variantes podem vir com `_especificação`
- Exceções: como classes
- Variáveis globais: mesmo para funções
- Funções e variáveis: `tudo_minusculo`
- Funções e argumentos para métodos: Sempre use `self` para o primeiro argumento para métodos de instância. Sempre use `cls` para o primeiro argumento para métodos de classe.
- Constantes: `MAI_USCU_LO`

#### Outros

---
Correto:
```py
if foo is not None:
    def f(x): return 2*x
```
Errado:
```py
if not foo is None:
    f = lambda x: 2*x
```

---

Correto:
```py
try:
    value = collection[key]
except KeyError:
    return key_not_found(key)
else:
    return handle_value(value)
```
Errado:

```py
try:
    # Muito curto
    return handle_value(collection[key])
except KeyError:
    # Vai pegar o mesmo erro
    return key_not_found(key)
```

---

Correto:
```py
with conn.begin_transaction():
    do_stuff_in_transaction(conn)
```
Errado:
```py
with conn:
    do_stuff_in_transaction(conn)
```

---

Correto:
```py
# Return None
def foo(x):
    if x >= 0:
        return math.sqrt(x)
    else:
        return None
```
Errado:
```py
def bar(x):
    if x < 0:
        return None
    return math.sqrt(x)
```

---

Correto:
```py
if foo.startswith('bar'):
```
Errado:

```py
if foo[:3] == 'bar':
```

---

Correto:
```py
if isinstance(obj, int):
```
Errado:
```py
if type(obj) is type(1):
```

---

Correto:
```py
if not seq:
if seq:
```
Errado:
```py
if len(seq):
if not len(seq):
```

---

Correto:
```py
if greeting:
```
Errado:
```py  
if greeting is True:
```

---


#### Como usaremos o código:

Com o visto acima e com os nomes reservados (`__init__`, `__name__` e `__main__`), que representam respectivamente o construtor de Classes, o "nome da execução" e o "tipo de execução", os códigos-padrão serão assim:

```py
# Usando os imports
from lxml import etree
from subprocess import Popen

import argpasre
import os

# Definição de funções
def get_ip(machine_name):
    pass

# Classes
class Scanner:
    def __init__(self):     # Nome reservado
        pass

# Main, com o nome reservado

if __name__ == ('__main__'):
    scan = Scanner()
    print('Hello')

```




