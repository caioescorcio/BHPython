import ftplib
import os
import socket
import win32file

def plain_ftp(docpath, server='192.168.100.98'):
    ftp = ftplib.FTP(server)
    ftp.login("anonymous", "anon@example.com")
    ftp.cwd('/pub/')
    ftp.storbinary("STOR " + os.path.basename(docpath), 
                   open(docpath, "rb"), 1024)
    ftp.quit()
    
def transmit(document_path):
    client = socket.socket()
    client.connect(('192.168.100.98', 9998))
    with open(document_path, 'rb') as f:
        win32file.TransmitFile(client,
                               win32file._get_osfhandle(f.fileno()),
                               0, 0, None, 0, b'', b'')
        
if __name__ == '__main__':
    transmit('C:\\Users\\caioe\\Documents\\Projetos\\BHPython\\c9\\codigos\\teste.txt')