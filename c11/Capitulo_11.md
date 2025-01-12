# Capítulo 11

Quando fui escrever esse texto, estava sem internet em casa e não pude baixar uma VM de Windows. Logo, não testei nada que está abaixo, pedi ajuda ao ChatGPT para documentar o capítulo e fiz algumas modificações. Recomendo fortemente que, se tiver interesse, leia esse capítulo no livro.

## Análise forense ofensiva

A forense tradicional é amplamente utilizada para investigar incidentes de segurança, como invasões e violações de dados. Contudo, as mesmas ferramentas também podem ser empregadas de maneira ofensiva para descobrir informações sensíveis em sistemas comprometidos. Este capítulo explora como utilizar o framework Volatility, originalmente projetado para defesa, como uma ferramenta ofensiva, destacando sua aplicação em snapshots de memória de máquinas virtuais (VMs).

### Instalação

Para utilizar o Volatility 3, o primeiro passo é configurar um ambiente de desenvolvimento isolado. Essa abordagem evita conflitos com dependências existentes no sistema principal e permite um trabalho mais organizado. No Windows, você pode iniciar criando um ambiente virtual com os seguintes comandos no PowerShell:

```powershell
python3 -m venv vol3
vol3/Scripts/Activate.ps1
cd vol3/
```

Esse ambiente virtual é essencial para garantir que todas as dependências necessárias sejam instaladas em um local separado. Em seguida, clone o repositório oficial do Volatility 3, que contém a última versão do framework:

```powershell
git clone https://github.com/volatilityfoundation/volatility3.git
cd volatility3/
```

Agora, instale o framework e suas dependências. O comando abaixo instala o Volatility diretamente no ambiente virtual:

```powershell
python setup.py install
pip install pycryptodome
```

A biblioteca `pycryptodome` é crucial para tarefas como decodificação de hashes, uma das funcionalidades exploradas mais adiante neste capítulo. Após concluir a instalação, você pode verificar as opções disponíveis no Volatility com:

```powershell
vol --help
```

Esse comando lista todos os plugins e parâmetros que o Volatility oferece, ajudando a orientar sua utilização.

### Reconhecimento geral


Uma das primeiras etapas em qualquer análise é compreender o sistema-alvo. O plugin `windows.info` é ideal para coletar informações gerais sobre a configuração do sistema operacional, kernel, arquitetura e outros detalhes cruciais. Por exemplo:

```powershell
vol -f <snapshot>.vmem windows.info
```

O comando retorna dados como:
- Versão exata do sistema operacional.
- Configuração do kernel.
- Tipo de processador (32 ou 64 bits).
- Núcleos e tempo de execução do sistema.

Essas informações ajudam a estabelecer um contexto sobre o ambiente analisado, fornecendo pistas sobre possíveis vulnerabilidades ou configurações errôneas.

O registro do Windows armazena uma vasta quantidade de informações sobre o sistema e suas operações. Usando o plugin `windows.registry.printkey`, é possível navegar por entradas específicas. Por exemplo, para listar todos os serviços instalados:

```powershell
vol -f <snapshot>.vmem windows.registry.printkey --key 'ControlSet001\Services'
```

A saída mostra os serviços instalados, suas chaves e valores. Essa informação é valiosa para identificar configurações incorretas ou serviços desnecessários que podem ser explorados.

### Reconhecimento do usuário

Uma análise detalhada dos processos em execução e seus argumentos pode revelar muito sobre o comportamento de um sistema e de seus usuários. O plugin `windows.cmdline` lista os comandos e argumentos utilizados para iniciar cada processo:

```powershell
vol -f <snapshot>.vmem windows.cmdline
```

Combine isso com o plugin `windows.pstree` para visualizar a hierarquia de processos:

```powershell
vol -f <snapshot>.vmem windows.pstree
```

Com esses dois comandos, você pode:
- Identificar processos que foram iniciados manualmente pelo usuário.
- Determinar relações entre processos pai e filho.
- Observar padrões suspeitos, como scripts automáticos ou ferramentas de administração remota.

Por exemplo, ao ver um processo de linha de comando (`cmd.exe`) seguido de um script ou utilitário não identificado, é possível que o usuário esteja executando operações sensíveis ou explorando vulnerabilidades.

### Reconhecimento de vulnerabilidades

Uma das principais metas de uma invasão é capturar hashes de senhas. Isso pode ser feito com o plugin `windows.hashdump`, que extrai hashes LM e NTLM:

```powershell
vol -f <snapshot>.vmem windows.hashdump
```

Os hashes obtidos podem ser:
- Crackeados offline com ferramentas como John the Ripper ou Hashcat.
- Utilizados diretamente em ataques de "pass-the-hash", permitindo acesso a outros recursos na rede sem conhecer a senha original.

Certifique-se de explorar cuidadosamente os hashes extraídos para avaliar quais são mais prováveis de serem utilizados ou vulneráveis.

O plugin `windows.malfind` é projetado para identificar regiões de memória que possuam código potencialmente injetado. Essas regiões são geralmente caracterizadas por permissões de leitura, gravação e execução. Para usá-lo, execute:

```powershell
vol -f <snapshot>.vmem windows.malfind
```

Isso ajuda a identificar malware que está operando na memória de processos confiáveis, uma técnica comum para evitar detecção.

Para entender as comunicações de rede de uma máquina, use o plugin `windows.netscan`. Ele lista todas as conexões ativas e encerradas no momento da captura do snapshot:

```powershell
vol -f <snapshot>.vmem windows.netscan
```

Conexões abertas em portas incomuns ou associadas a processos não reconhecidos podem indicar atividades maliciosas, como backdoors ou ferramentas de exfiltração de dados.

## A interface volshell

A interface interativa `volshell` é uma ferramenta poderosa que permite explorar snapshots de maneira personalizada. Ao iniciá-la:

```powershell
volshell -w -f <snapshot>.vmem
```

Você obtém acesso a um ambiente Python interativo, onde pode carregar plugins, criar funções e realizar análises específicas diretamente. Isso é úteis em casos onde os plugins padrão não atendem às suas necessidades.

## Plugins personalizados do Volatility

**OBSERVAÇÃO**: Leia essa parte no livro, pois não escrevi nem estudei os códigos por falta de recursos ao tempo de se fazer esse Markdown

A criação de plugins customizados é baseada em uma estrutura definida. Um exemplo básico seria:

```python
class CustomPlugin(interfaces.plugin.PluginInterface):
    @classmethod
    def get_requirements(cls):
        pass

    def run(self):
        pass
```

O ASLR (Address Space Layout Randomization) é uma técnica de segurança que randomiza os endereços de memória de processos para dificultar explorações. Um plugin para verificar quais processos não estão protegidos poderia ser estruturado assim:

```python
class AslrCheck(interfaces.plugin.PluginInterface):
    def run(self):
        # Implementação para identificar processos sem ASLR
        pass
```

Esse tipo de plugin pode identificar pontos fracos em sistemas modernos, onde a maioria dos processos deveria estar protegida por padrão.

### Explorando o código

Experimente diferentes snapshots para observar comportamentos e vulnerabilidades:

```powershell
vol -p ./plugins/windows -f <snapshot>.vmem <plugin>
```

Essa abordagem permite validar plugins e descobrir informações detalhadas sobre os alvos.

Abaixo estão algumas interfces de memória que podem ser usadas para testes:

- [PassMark Software](https://www.osforensics.com/tools/volatility-workbench.html)
- [Volatility Foundation](https://github.com/volatilityfoundation/volatility/wiki/Memory-Samples)



