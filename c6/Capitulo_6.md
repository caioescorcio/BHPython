# Capitulo 6 

Neste capítulo, dedicaremos um tempo para o estudo do software Burp Suite, da PortSwigger. 

## Estendendo o proxy do Burp

Primeiramente, para este capítulo, vale mencionar que, se você alguma vez já mexeu com segurança/invasão de aplicações web, provavelmente você já utilizou o BurpSuite. Ele oferece uma série de funcionalidades para o usuário, desde *spiders* (que rastreiam um pacote até seu endereço de destino final) até mesmo *proxy*, que é um tópico já estudado em outros capítulos. O proxy do Burp é diferente do nosso pois ele capta e modifica pacotes por meio de uma interface, que facilita o trabalho.

Agora, como objetivos, serão explorados algumas funcionalidades específicas do Burp, as extensões. Nossa meta é entender como elas são feitas e como podemos usá-las para técnicas de exploração. Nós iremos criar 3 extensões:

- Uma para utilizar uma solicitação HTTP interceptada pelo proxy como base para um [fuzzer de mutação](https://pt.wikipedia.org/wiki/Fuzzing) que, por sua vez, será usado no Intruder. Basicamente uma técnica de criar um fuzzer usando o Proxy e executá-lo
- Outra para se comunicar com a API da Microsoft Bing para mostrar todos os hosts virtuais localizados no mesmo endereço de IP do site de destino, além dos subdomínios detectados para o doínio de destino.
- Por fim, uma extensão para gerar uma wordlist com base em um site de destino para uso em ataques de força bruta.

### Configurando o Burp Suite

Nas máquinas Kali, ele já vem instalado por default. Contudo, como estou utilizando Windows, instalei-o através do [link de download](https://portswigger.net/burp/releases/). 

Além disso, será necessária a [instalação do Jython](https://repo1.maven.org/maven2/org/python/jython-standalone/), uma implementação do Python 2 feita em Java. Como o Jython utiliza o Python 2, os autores abriram uma execeção no andamento do livro (que até então era exclusivamente em Python 3) para utilizá-lo. Eles instruem para instalar a versão pelo instalador Standalone e salvar o seu .JAR em um local de fácil acesso.

Para rodar o Jython use:

```bash
java -jar jython-standalone-2.7.4.jar codigo.py
```

Com o Burp inicializado, clique na guia *Settings*, vá em *Extensions* e procure o JAR da versão Standalone lá:

![burpsetup](../imagens/burpsetup.png)

### Realizando fuzzing com o Burp





