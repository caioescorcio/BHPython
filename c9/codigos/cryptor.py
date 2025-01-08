from Cryptodome.Cipher import AES, PKCS1_OAEP
from Cryptodome.PublicKey import RSA
from Cryptodome.Random import get_random_bytes
from io import BytesIO

import base64
import zlib

def generate():
    new_key = RSA.generate(2048)
    private_key = new_key.export_key()
    public_key = new_key.publickey().export_key()
    
    with open('key.pri', 'wb') as f:
        f.write(private_key)
        
    with open('key.pub', 'wb') as f:
        f.write(public_key)
        
def get_rsa_cipher(keytype):
    with open(f'key.{keytype}') as f:
        key = f.read()
    rsa_key = RSA.import_key(key)
    return (PKCS1_OAEP.new(rsa_key), rsa_key.size_in_bytes())

def encrypt(plaintext):
    compressed_text = zlib.compress(plaintext)
    
    session_key = get_random_bytes(16)
    cipher_aes = AES.new(session_key, AES.MODE_EAX)
    cipher_text, tag = cipher_aes.encrypt_and_digest(compressed_text)
    
    cipher_rsa, _ = get_rsa_cipher('pub')
    encrypted_session_key = cipher_rsa.encrypt(session_key)
    
    msg_payload = encrypted_session_key + cipher_aes.nonce + tag + cipher_text
    encrypted = base64.encodebytes(msg_payload)
    return encrypted
    
def decrypt(encrypted):
    encrypted_bytes = BytesIO(base64.decodebytes(encrypted))
    cipher_rsa, keysize_in_bytes = get_rsa_cipher('pri')
    
    encrypted_session_key = encrypted_bytes.read(keysize_in_bytes)
    nonce = encrypted_bytes.read(16)
    tag = encrypted_bytes.read(16)
    ciphertext = encrypted_bytes.read()
    
    session_key = cipher_rsa.decrypt(encrypted_session_key)
    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
    decrypted = cipher_aes.decrypt_and_verify(ciphertext, tag)
    
    plaintext = zlib.decompress(decrypted)
    return plaintext


if __name__ == '__main__':
    # generate()
    
    plaintext = b'TESTE '
    print(decrypt(encrypt(plaintext)))
  