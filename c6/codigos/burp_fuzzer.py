from burp import IBurpExtender
from burp import IIntruderPayloadGeneratorFactory
from burp import IIntruderPayloadGenerator

from java.util import List, ArrayList

import random

class BurpExtender(IBurpExtender, IIntruderPayloadGeneratorFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers   = callbacks.getHelpers()
        
        callbacks.registerIntruderPayloadGeneratorFactory(self)
        
        return
    
    def getGeneratorName(self):
        return "BHP Payload Generator"
    
    def createNewInstance(self, attack):
        return BHPFuzzer(self,attack)
    
class BHPFuzzer(IIntruderPayloadGenerator):
    def __init__(self, extender, attack):
        self._extender          = extender
        self._helpers           = extender._helpers
        self._attack            = attack
        self.max_payloads       = 1000
        self.num_interactions   = 0
        
        return
    
    def hasMorePayloads(self):
        if self.num_interactions == self.max_payloads:
            return False
        else: 
            return True
    
    def getNextPayload(self, current_payload):
        # Converter para string
        payload = "".join(chr(x) for x in current_payload)
        
        # Chama o nosso mutador simples para realizar fuzzing no POST
        payload = self.mutate_payload(payload)
        
        # Aumenta o numero de tentativas de fuzzing
        self.num_interactions += 1
        
        return payload
    
    def reset(self):
        self.num_interactions = 0
        return
    
    def mutate_payload(self, original_payload):
        # Escolher um mutador simples ou ateh mesmo chamar um script externo
        picker = random.randint(1, 3)
        
        # Selecionar o descolamento aleatorio no payload para mutacao
        offset = random.randint(0, len(original_payload) - 1)
        
        # Divide a string original no offset (front = ateh offset, back = depois do offset)
        front, back = original_payload[:offset], original_payload[offset:]  
        
        # Tentativa de inserir uma injecao de SQL no deslocamento aleatorio
        if picker == 1:
            front += "'"
            
        # Inserir uma tentativa de XSS
        elif picker == 2:
            front += "<script>alert('AAAAA');</script>"
            
        # Repetir um trecho aleatorio do payload original
        elif picker == 3:
            chunk_lenght = random.randint(0, len(back) - 1)
            repeater = random.randint(1, 10)
            for _ in range(repeater):
                front += original_payload[:offset + chunk_lenght]
        
        return front + back
        
        
        