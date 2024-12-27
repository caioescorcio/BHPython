import paramiko

def ssh_command(ip, port, user, password, cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, port=port, username=user, password=password)

    _, stdout, stderr = client.exec_command(cmd)
    output = stdout.readlines() + stderr.readlines()

    if output:
        print("--- Saída ---")
        for line in output:
            print(line.strip())

if __name__ == '__main__':
    import getpass
    # user = getpass.getuser()
    user = input("Username: ")
    password = getpass.getpass()

    ip = input('Insira o IP do servidor: ') or '127.0.0.1'
    port = input('Insira a porta ou <CR>: ') or 9000
    cmd = input('Insira o comando ou <CR>: ') or 'id'
    ssh_command(ip, port, user, password, cmd)