import os

def run(**args):
    print("[*] No módulo dirlister.")
    files = os.listdir(".")
    return str(files)