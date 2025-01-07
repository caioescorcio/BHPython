import binascii

# Shellcode inofensivo que abre o Notepad no Windows
shellcode = (
    b"\x31\xc0"              # xor eax, eax         ; Zera o registrador eax
    b"\x50"                  # push eax             ; Coloca NULL no topo da pilha
    b"\x68\x2e\x65\x78\x65"  # push ".exe"          ; Coloca ".exe" no topo da pilha
    b"\x68\x6f\x74\x65\x70"  # push "notep"         ; Coloca "notep" no topo da pilha
    b"\x8b\xcc"              # mov ecx, esp         ; Aponta ecx para "notepad.exe"
    b"\x50"                  # push eax             ; NULL como argumento (para os parâmetros do programa)
    b"\x51"                  # push ecx             ; Aponta para "notepad.exe"
    b"\xb8\xc7\x93\xc2\x77"  # mov eax, 0x77c293c7  ; Endereço da função WinExec
    b"\xff\xd0"              # call eax             ; Chama WinExec
    b"\x31\xdb"              # xor ebx, ebx         ; Zera o registrador ebx
    b"\x31\xc0"              # xor eax, eax         ; Zera eax novamente
    b"\x40"                  # inc eax              ; eax = 1
    b"\xcd\x80"              # int 0x80             ; Finaliza o programa
)

# Nome do arquivo onde o shellcode será salvo
output_filename = "shellcode.bin"

# Salvar o shellcode em um arquivo binário
with open(output_filename, "wb") as file:
    file.write(shellcode)

print(f"Shellcode salvo em: {output_filename}")
