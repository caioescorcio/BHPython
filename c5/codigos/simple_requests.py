import urllib.parse
import urllib.request
import requests


# post data
info = {'user': 'caio', 'passwd': '123412'}
url = 'http://boodelyboo.com'


# urllib

# get 
with urllib.request.urlopen(url) as response:
    content = response.read()
print(content)    

# post
data = urllib.parse.urlencode(info).encode()    # converte para bytes
req = urllib.request.Request(url, data)         # gera a requisicao

with urllib.request.urlopen(req) as response:   # faz e le a resposta da requisicao
    content = response.read()
print(content)


# requests

# post
response = requests.post(url, data=data)
print(response.text)        # response.text = string; response.content = bytestring

